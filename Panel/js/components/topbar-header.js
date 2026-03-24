/**
 * Topbar Header Web Component
 * ValVic CRM
 */
class TopbarHeader extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        this.title = this.getAttribute('title') || 'Panel ValVic';
        this.render();
        this.setupEvents();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                @import url('css/panel.css');
                @import url('https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css');
                :host {
                    display: contents; /* Ensure layout works correctly inside desk wrapper */
                }
                .logout-topbar {
                    background: transparent;
                    border: 1px solid var(--border);
                    color: var(--ink3);
                    cursor: pointer;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    font-family: inherit;
                    font-size: 0.875rem;
                    transition: all 0.3s ease;
                    margin-left: 1rem;
                }
                .logout-topbar:hover {
                    color: rgba(239, 68, 68, 1);
                    border-color: rgba(239, 68, 68, 0.4);
                    background: rgba(239, 68, 68, 0.05);
                }
                .profile-section {
                    display: flex;
                    align-items: center;
                }
            </style>
            <header class="topbar">
                <button class="topbar-menu-btn" id="btn-menu" type="button" aria-label="Abrir menú">
                    <i class="ph ph-list" aria-hidden="true"></i>
                </button>

                <h1 class="topbar-title" id="topbar-negocio">
                    <slot name="title">${this.title}</slot>
                </h1>

                <div class="user-profile profile-section">
                    <div class="user-info">
                        <span class="user-name" id="user-display-name">Cargando…</span>
                        <span class="user-role">Administrador</span>
                    </div>
                    <div class="user-avatar" id="user-avatar" aria-hidden="true">VV</div>
                    
                    <button class="logout-topbar" id="btn-logout-topbar" type="button" aria-label="Cerrar sesión">
                        <i class="ph ph-sign-out" aria-hidden="true"></i>
                        <span class="hide-mobile">Cerrar Sesión</span>
                    </button>
                </div>
            </header>
        `;
    }

    setupEvents() {
        const btnMenu = this.shadowRoot.getElementById('btn-menu');
        if (btnMenu) {
            btnMenu.addEventListener('click', () => {
                // Fire an event to be caught by sidebar-nav
                document.dispatchEvent(new CustomEvent('toggle-sidebar'));
            });
        }

        const btnLogout = this.shadowRoot.getElementById('btn-logout-topbar');
        if (btnLogout) {
            btnLogout.addEventListener('click', async () => {
                try {
                    const response = await fetch('/api/auth/logout', { method: 'POST' });
                    if (response.ok) {
                        window.location.href = 'login.html';
                    } else {
                        console.error('Logout failed');
                        window.location.href = 'login.html'; // fallback
                    }
                } catch (error) {
                    console.error('Error in logout:', error);
                    window.location.href = 'login.html'; // fallback
                }
            });
        }
    }
}

customElements.define('topbar-header', TopbarHeader);
