document.addEventListener('DOMContentLoaded', function() {
    // Property selection change in add tenant form
    const propertySelect = document.getElementById('property_id');
    
    if (propertySelect) {
        const unitContainer = document.getElementById('unit-container');
        const unitSelect = document.getElementById('unit_id');
        
        propertySelect.addEventListener('change', function() {
            const propertyId = this.value;
            
            if (!propertyId) {
                unitContainer.style.display = 'none';
                return;
            }
            
            // Check if property is a multi-unit property
            fetch(`/api/property-details/${propertyId}`)
                .then(response => response.json())
                .then(property => {
                    if (property.type === 'Tenement' || property.type === 'Shop') {
                        // Get units for this property
                        fetch(`/properties/available-units/${propertyId}`)
                            .then(response => response.json())
                            .then(units => {
                                unitSelect.innerHTML = '<option value="">-- Select Unit --</option>';
                                
                                units.forEach(unit => {
                                    const option = document.createElement('option');
                                    option.value = unit.id;
                                    option.textContent = `${unit.unit_name} (₦${unit.price.toLocaleString()})`;
                                    unitSelect.appendChild(option);
                                });
                                
                                unitContainer.style.display = 'block';
                            });
                    } else {
                        unitContainer.style.display = 'none';
                    }
                });
        });
        
        // Set today as default for lease start date
        const startDateField = document.getElementById('lease_start_date');
        if (startDateField && !startDateField.value) {
            startDateField.valueAsDate = new Date();
        }
        
        // Set default lease end date (1 year from start date)
        const endDateField = document.getElementById('lease_end_date');
        if (endDateField && !endDateField.value) {
            const oneYearFromNow = new Date();
            oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1);
            endDateField.valueAsDate = oneYearFromNow;
        }
        
        // Update end date when start date changes
        if (startDateField && endDateField) {
            startDateField.addEventListener('change', function() {
                const startDate = new Date(this.value);
                const endDate = new Date(startDate);
                endDate.setFullYear(endDate.getFullYear() + 1);
                endDateField.valueAsDate = endDate;
            });
        }
    }
    
    // Search functionality in tenants list
    const tenantSearchInput = document.getElementById('tenantSearch');
    
    if (tenantSearchInput) {
        const table = document.getElementById('tenantsTable');
        
        if (table) {
            const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
            
            tenantSearchInput.addEventListener('keyup', function() {
                const term = this.value.toLowerCase();
                
                for (let i = 0; i < rows.length; i++) {
                    const cells = rows[i].getElementsByTagName('td');
                    let visible = false;
                    
                    for (let j = 0; j < cells.length; j++) {
                        if (cells[j].textContent.toLowerCase().indexOf(term) > -1) {
                            visible = true;
                            break;
                        }
                    }
                    
                    rows[i].style.display = visible ? '' : 'none';
                }
            });
        }
    }
});