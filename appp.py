# ---- Landlord account statement routes (add to app.py) ----

@app.route('/landlords/account-statement')
@login_required
def landlord_account_statement():
    conn = get_db_connection()
    landlords = conn.execute('''
        SELECT l.*, 
               (SELECT COUNT(*) FROM properties p WHERE p.landlord_id = l.id) as total_properties
        FROM landlords l
        ORDER BY l.full_name COLLATE NOCASE
    ''').fetchall()
    conn.close()
    return render_template('landlords/landlord_account_statement.html', landlords=landlords)


@app.route('/landlords/<int:landlord_id>/account-statement')
@login_required
def landlord_account_detail(landlord_id):
    conn = get_db_connection()
    landlord = conn.execute('SELECT * FROM landlords WHERE id = ?', (landlord_id,)).fetchone()
    if not landlord:
        flash('Landlord not found.', 'danger')
        conn.close()
        return redirect(url_for('landlord_account_statement'))

    # 1) Payments made by tenants for properties belonging to this landlord
    payments = conn.execute('''
        SELECT 
            p.id as payment_id,
            p.payment_date as date,
            p.description as narration,
            p.payment_method as mode_of_payment,
            p.amount as amount,
            t.full_name as tenant_name,
            'payment' as source
        FROM payments p
        LEFT JOIN tenants t ON p.tenant_id = t.id
        LEFT JOIN properties prop ON p.property_id = prop.id
        WHERE prop.landlord_id = ?
    ''', (landlord_id,)).fetchall()

    # 2) Manual landlord transactions from new table
    manual = conn.execute('''
        SELECT 
            lt.id as txn_id,
            lt.date as date,
            lt.narration as narration,
            lt.payment_method as mode_of_payment,
            lt.amount as amount,
            lt.transaction_type as txn_type,
            'manual' as source
        FROM landlord_transactions lt
        WHERE lt.landlord_id = ?
    ''', (landlord_id,)).fetchall()

    conn.close()

    # Normalize into common list of dicts with credit/debit fields and a date type
    merged = []
    for p in payments:
        merged.append({
            'date': p['date'],
            'narration': p['narration'] or f"Payment from {p['tenant_name'] or 'Unknown tenant'}",
            'mode_of_payment': p['mode_of_payment'] or '',
            'credit': float(p['amount'] or 0),
            'debit': 0.0,
            'source': 'payment',
            'meta_id': p['payment_id']
        })

    for m in manual:
        if (m['txn_type'] or '').lower() == 'credit':
            credit = float(m['amount'] or 0)
            debit = 0.0
        else:
            credit = 0.0
            debit = float(m['amount'] or 0)
        merged.append({
            'date': m['date'],
            'narration': m['narration'] or '',
            'mode_of_payment': m['mode_of_payment'] or '',
            'credit': credit,
            'debit': debit,
            'source': 'manual',
            'meta_id': m['txn_id']
        })

    # Sort by date ascending (older first). If dates are strings in YYYY-MM-DD it's fine.
    merged.sort(key=lambda x: x['date'] or '')

    # Compute running balance
    balance = 0.0
    detailed = []
    for i, tx in enumerate(merged, start=1):
        balance += (tx['credit'] or 0) - (tx['debit'] or 0)
        detailed.append({
            'sn': i,
            'date': tx['date'],
            'narration': tx['narration'],
            'mode_of_payment': tx.get('mode_of_payment', ''),
            'credit': tx['credit'],
            'debit': tx['debit'],
            'balance': balance,
            'source': tx['source'],
            'meta_id': tx['meta_id']
        })

    return render_template(
        'landlords/landlord_account_detail.html',
        landlord=landlord,
        transactions=detailed,
        balance=balance
    )


@app.route('/landlords/<int:landlord_id>/add-statement', methods=['GET', 'POST'])
@login_required
def add_landlord_transaction(landlord_id):
    """
    Add a manual credit or debit transaction to landlord_transactions table.
    """
    conn = get_db_connection()
    landlord = conn.execute('SELECT * FROM landlords WHERE id = ?', (landlord_id,)).fetchone()
    if not landlord:
        conn.close()
        flash('Landlord not found.', 'danger')
        return redirect(url_for('landlord_account_statement'))

    if request.method == 'POST':
        # Validate input
        date = request.form.get('date') or None
        txn_type = request.form.get('type')  # 'credit' or 'debit'
        narration = request.form.get('narration', '').strip()
        mode_of_payment = request.form.get('mode_of_payment', '').strip()
        amount_raw = request.form.get('amount', '0').strip()

        try:
            amount = float(amount_raw)
        except ValueError:
            conn.close()
            flash('Enter a valid amount.', 'danger')
            return redirect(url_for('add_landlord_transaction', landlord_id=landlord_id))

        if txn_type not in ('credit', 'debit'):
            conn.close()
            flash('Select transaction type (credit or debit).', 'danger')
            return redirect(url_for('add_landlord_transaction', landlord_id=landlord_id))

        if not date:
            # default to today
            from datetime import date as dt_date
            date = dt_date.today().isoformat()

        # insert into landlord_transactions
        conn.execute('''
            INSERT INTO landlord_transactions (landlord_id, date, narration, transaction_type, amount, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (landlord_id, date, narration, txn_type, amount, mode_of_payment))
        conn.commit()
        conn.close()

        flash('Transaction saved.', 'success')
        return redirect(url_for('landlord_account_detail', landlord_id=landlord_id))

    conn.close()
    return render_template('landlords/add_landlord_transaction.html', landlord=landlord)
