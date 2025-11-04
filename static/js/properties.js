document.addEventListener('DOMContentLoaded', function() {
    // Rent property buttons handling
    const rentButtons = document.querySelectorAll('.rent-btn');
    
    if (rentButtons.length > 0) {
        rentButtons.forEach(button => {
            button.addEventListener('click', function() {
                const propertyId = this.getAttribute('data-property-id');
                const propertyType = this.getAttribute('data-property-type');
                
                document.getElementById('rent_property_id').value = propertyId;
                const unitSelectionContainer = document.getElementById('unit-selection-container');
                
                if (propertyType === 'multi') {
                    // Get available units
                    fetch(`/properties/available-units/${propertyId}`)
                        .then(response => response.json())
                        .then(units => {
                            const unitSelect = document.getElementById('unit_id');
                            unitSelect.innerHTML = '<option value="">-- Select Unit --</option>';
                            
                            units.forEach(unit => {
                                const option = document.createElement('option');
                                option.value = unit.id;
                                option.textContent = `${unit.unit_name} (₦${unit.price.toLocaleString()})`;
                                unitSelect.appendChild(option);
                            });
                            
                            unitSelectionContainer.style.display = 'block';
                            const modal = new bootstrap.Modal(document.getElementById('rentPropertyModal'));
                            modal.show();
                        })
                        .catch(error => {
                            console.error('Error fetching units:', error);
                            Swal.fire({
                                title: 'Error',
                                text: 'Failed to load available units',
                                icon: 'error',
                                confirmButtonText: 'OK'
                            });
                        });
                } else {
                    // Single property
                    unitSelectionContainer.style.display = 'none';
                    const modal = new bootstrap.Modal(document.getElementById('rentPropertyModal'));
                    modal.show();
                }
            });
        });
    }
    
    // Property type selection handling in add property form
    const typeSelect = document.getElementById('type');
    
    if (typeSelect) {
        const priceContainer = document.getElementById('price-container');
        const unitsContainer = document.getElementById('units-container');
        
        typeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            
            if (selectedType === 'Tenement' || selectedType === 'Shop') {
                priceContainer.style.display = 'none';
                unitsContainer.style.display = 'flex';
            } else {
                priceContainer.style.display = 'block';
                unitsContainer.style.display = 'none';
                // Clear units fields
                document.getElementById('units-fields-container').innerHTML = '';
            }
        });
        
        // Generate unit fields
        const generateUnitsBtn = document.getElementById('generate-units-btn');
        
        if (generateUnitsBtn) {
            generateUnitsBtn.addEventListener('click', function() {
                const numUnits = parseInt(document.getElementById('num_units').value) || 0;
                const container = document.getElementById('units-fields-container');
                
                // Clear previous fields
                container.innerHTML = '';
                
                if (numUnits < 1) {
                    Swal.fire({
                        title: 'Error',
                        text: 'Please enter a valid number of units (at least 1)',
                        icon: 'error',
                        confirmButtonText: 'OK'
                    });
                    return;
                }
                
                // Create unit fields
                for (let i = 1; i <= numUnits; i++) {
                    const unitRow = document.createElement('div');
                    unitRow.className = 'row border-top pt-3 mt-3';
                    unitRow.innerHTML = `
                        <h5 class="mb-3">Unit #${i}</h5>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="unit_name_${i}" class="form-label">Unit Name/Number <span class="text-danger">*</span></label>
                                <input type="text" class="form-control" id="unit_name_${i}" name="unit_name_${i}" required>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="unit_size_${i}" class="form-label">Size</label>
                                <input type="text" class="form-control" id="unit_size_${i}" name="unit_size_${i}">
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="mb-3">
                                <label for="unit_price_${i}" class="form-label">Rent Price <span class="text-danger">*</span></label>
                                <div class="input-group">
                                    <span class="input-group-text">₦</span>
                                    <input type="number" class="form-control" id="unit_price_${i}" name="unit_price_${i}" min="0" step="0.01" required>
                                </div>
                            </div>
                        </div>
                    `;
                    container.appendChild(unitRow);
                }
            });
        }
    }
});