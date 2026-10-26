// Phone number validation
(() => {
    'use strict';
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.querySelectorAll('input').forEach(input => {
            input.addEventListener('input',()=>{
                if (input.value.trim() === '') {
                    input.classList.remove('is-valid', 'is-invalid');
                    return;
                }

                if (input.checkValidity()) {
                    input.classList.add('is-valid');
                    input.classList.remove('is-invalid');
                } else {
                    input.classList.add('is-invalid');
                    input.classList.remove('is-valid');
                }
            });
        });

        form.querySelectorAll('select').forEach(select =>{
            select.addEventListener('change', () => {
                if (select.checkValidity()) {
                    select.classList.add('is-valid');
                    select.classList.remove('is-invalid');
                } else {
                    select.classList.add('is-invalid');
                    select.classList.remove('is-valid');
                }
            });
        });
        
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
})();

// Password Validation
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirm_password");
if (password && confirmPassword){
    function validatePassword() {
        if(confirmPassword.value ===""){
            confirmPassword.setCustomValidity("");
        } else if (password.value!==confirmPassword.value){
            confirmPassword.setCustomValidity("Passwords do not match.")
        } else{
            confirmPassword.setCustomValidity("")
        }

        if (confirmPassword.value !== ""){
            confirmPassword.classList.toggle(
                'is-valid',confirmPassword.checkVisibility()
            );
            confirmPassword.classList.toggle(
                "is-invalid",
                !confirmPassword.checkValidity()
            );
        }
    }
    password.addEventListener("input", validatePassword);
    confirmPassword.addEventListener("input", validatePassword);
}


// Bootstrap Toast
document.querySelectorAll('.toast').forEach(function (toastElement) {
    const toast = bootstrap.Toast.getOrCreateInstance(toastElement, {
        delay: 3000
    });
    toast.show();
});

