/**
 * Sidebar Navigation Web Component
 * ValVic CRM
 */
class SidebarNav extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.render();
        this.setupActiveLink();
        this.setupEvents();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('css/panel.css');
                @import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');
                :host {
                    display: contents; /* Ensure layout works correctly inside main wrapper */
                }
            </style>
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-glow" id="sidebar-glow"></div>
                <a href="https://valvic.cl" class="brand" aria-label="ValVic inicio">
                    <img src="favicon-180-transparent.png" alt="ValVic" class="brand-icon" width="30" height="30" loading="lazy">
                    ValVic
                </a>

                <nav class="nav-menu" role="navigation" aria-label="Menú principal">
                    <a href="agenda.html" class="nav-link" id="nav-dashboard" aria-label="Dashboard">
                        <i class="ph ph-squares-four nav-icon" aria-hidden="true"></i>
                        Dashboard
                    </a>
                    <a href="agenda.html" class="nav-link" aria-label="Agenda de citas">
                        <i class="ph ph-calendar-blank nav-icon" aria-hidden="true"></i>
                        Agenda / Citas
                    </a>
                    <a href="pacientes.html" class="nav-link" aria-label="CRM de clientes">
                        <i class="ph ph-users nav-icon" aria-hidden="true"></i>
                        Clientes CRM
                    </a>
                    <a href="configuracion.html" class="nav-link" aria-label="Configuración de IA Vicky">
                        <i class="ph ph-robot nav-icon" aria-hidden="true"></i>
                        IA de Vicky
                    </a>
                    <div class="nav-spacer"></div>
                    <a href="configuracion.html" class="nav-link nav-link--muted" aria-label="Configuración">
                        <i class="ph ph-gear nav-icon" aria-hidden="true"></i>
                        Configuración
                    </a>
                </nav>
            </aside>
            <div class="sidebar-overlay" id="sidebar-overlay" aria-hidden="true"></div>
        `;
    }

    setupActiveLink() {
        const path = window.location.pathname;
        const page = path.split('/').pop().split('?')[0].split('#')[0] || 'agenda.html';
        
        const links = this.shadowRoot.querySelectorAll('.nav-link');
        links.forEach(link => {
            link.classList.remove('active');
            link.removeAttribute('aria-current');
            
            const href = link.getAttribute('href');
            if (href && href === page) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            }
        });
    }

    setupEvents() {
        // Toggle mobile sidebar via document events from topbar
        document.addEventListener('toggle-sidebar', () => {
            const sidebar = this.shadowRoot.getElementById('sidebar');
            const overlay = this.shadowRoot.getElementById('sidebar-overlay');
            if (sidebar && overlay) {
                const isOpen = sidebar.classList.contains('sidebar--open');
                if (isOpen) {
                    sidebar.classList.remove('sidebar--open');
                    overlay.classList.remove('sidebar-overlay--open');
                    overlay.setAttribute('aria-hidden', 'true');
                } else {
                    sidebar.classList.add('sidebar--open');
                    overlay.classList.add('sidebar-overlay--open');
                    overlay.removeAttribute('aria-hidden');
                }
            }
        });
        
        // overlay click to close
        const overlay = this.shadowRoot.getElementById('sidebar-overlay');
        if (overlay) {
            overlay.addEventListener('click', () => {
                const sidebar = this.shadowRoot.getElementById('sidebar');
                if (sidebar) sidebar.classList.remove('sidebar--open');
                overlay.classList.remove('sidebar-overlay--open');
                overlay.setAttribute('aria-hidden', 'true');
            });
        }

        // Sidebar Glow Effect
        const sidebar = this.shadowRoot.getElementById('sidebar');
        const glow = this.shadowRoot.getElementById('sidebar-glow');
        if (sidebar && glow) {
            sidebar.addEventListener('mousemove', (e) => {
                const rect = sidebar.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                glow.style.left = x + 'px';
                glow.style.top = y + 'px';
                glow.classList.add('active');
            });
            sidebar.addEventListener('mouseleave', () => {
                glow.classList.remove('active');
            });
        }
    }
}

customElements.define('sidebar-nav', SidebarNav);
