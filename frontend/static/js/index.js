// index.js

// Initialize particles.js with your custom configuration
particlesJS('particles-js', {
    particles: {
        number: {
            value: 100, // Number of particles
            density: {
                enable: true,
                value_area: 800 // Density of particles
            }
        },
        color: {
            value: '#00ff00' // Neon green color for particles
        },
        shape: {
            type: 'circle', // Particle shape
        },
        opacity: {
            value: 0.5, // Opacity of particles
            random: true,
            anim: {
                enable: true,
                speed: 1,
                opacity_min: 0.1,
                sync: false
            }
        },
        size: {
            value: 3, // Particle size
            random: true,
            anim: {
                enable: true,
                speed: 4,
                size_min: 0.1,
                sync: false
            }
        },
        move: {
            enable: true,
            speed: 1,
            direction: 'none',
            random: false,
            straight: false,
            out_mode: 'out',
            bounce: false,
            attract: {
                enable: false,
                rotateX: 600,
                rotateY: 1200
            }
        }
    },
    interactivity: {
        events: {
            onhover: {
                enable: true,
                mode: 'repulse' // Particles move away from the cursor on hover
            },
            onclick: {
                enable: true,
                mode: 'push' // Add more particles on click
            }
        },
        modes: {
            repulse: {
                distance: 100,
                duration: 0.4
            },
            push: {
                particles_nb: 4
            }
        }
    },
    retina_detect: true
});
