document.addEventListener('DOMContentLoaded', function() {
    const estrelasContainer = document.getElementById('estrelas-bg');
    const numeroDeEstrelas = 150;

    for (let i = 0; i < numeroDeEstrelas; i++) {
        let estrela = document.createElement('div');
        estrela.classList.add('estrela');

        let tamanho = Math.random() * 3 + 1;
        estrela.style.width = `${tamanho}px`;
        estrela.style.height = `${tamanho}px`;

        estrela.style.top = `${Math.random() * 100}%`;
        estrela.style.left = `${Math.random() * 100}%`;

        // Para um efeito mais dinâmico, varia a duração da animação de piscar
        estrela.style.animationDuration = `${Math.random() * 3 + 2}s`;
        // Varia o início da animação para não piscarem todas juntas
        estrela.style.animationDelay = `${Math.random() * 3}s`;

        estrelasContainer.appendChild(estrela);
    }
}); 