const btns = document.querySelectorAll('.details')

btns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        // e.preventDefault();
        const parent = e.target.closest('.alert');
        const modal = parent.querySelector('.modal');
        const close = modal.querySelector('.close')
        modal.style.display = 'block'

        window.onclick = (e) => {
            if (e.target == modal) {
                modal.style.display = 'none';
            }
        }

        close.onclick = () => {
            modal.style.display = 'none';
        }
    })
});