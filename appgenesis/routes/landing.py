from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def landing_page():
    """Public landing page for Verbo da Vida Braga."""
    html = """
    <!DOCTYPE html>
    <html lang="pt-PT">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="Verbo da Vida Braga - Portal de Gestão Administrativo e Membro">
        <meta name="theme-color" content="#1f2937">
        <title>Verbo da Vida Braga - Genesis</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            html, body {
                height: 100%;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1f2937;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1rem;
            }

            .container {
                max-width: 900px;
                width: 100%;
                background: white;
                border-radius: 2rem;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                overflow: hidden;
            }

            .hero {
                display: grid;
                grid-template-columns: 1fr 1fr;
                min-height: 600px;
                gap: 3rem;
                align-items: center;
                padding: 4rem 3rem;
            }

            .hero-content h1 {
                font-size: clamp(1.75rem, 5vw, 3rem);
                font-weight: 700;
                margin-bottom: 1rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            .hero-content p {
                font-size: 1.125rem;
                color: #6b7280;
                margin-bottom: 2rem;
                line-height: 1.8;
            }

            .cta-button {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 0.5rem;
                text-decoration: none;
                font-weight: 600;
                font-size: 1.0625rem;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
            }

            .cta-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
            }

            .cta-button:active {
                transform: translateY(0);
            }

            .hero-visual {
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
                border-radius: 1.5rem;
                min-height: 400px;
            }

            .hero-visual-content {
                text-align: center;
            }

            .hero-visual-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
            }

            .hero-visual-text {
                color: #6b7280;
                font-size: 1rem;
                font-weight: 500;
            }

            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-top: 2rem;
            }

            .feature {
                padding: 1.5rem;
                background: #f9fafb;
                border-radius: 0.75rem;
                border-left: 4px solid #667eea;
            }

            .feature-title {
                font-weight: 600;
                margin-bottom: 0.5rem;
                color: #1f2937;
            }

            .feature-description {
                color: #6b7280;
                font-size: 0.9375rem;
            }

            footer {
                background: #f3f4f6;
                padding: 1.5rem 3rem;
                text-align: center;
                color: #6b7280;
                font-size: 0.875rem;
                border-top: 1px solid #e5e7eb;
            }

            @media (max-width: 768px) {
                .hero {
                    grid-template-columns: 1fr;
                    padding: 2rem 1.5rem;
                    gap: 2rem;
                    min-height: auto;
                }

                .hero-visual {
                    min-height: 250px;
                }

                .hero-content h1 {
                    font-size: 1.75rem;
                }

                .hero-content p {
                    font-size: 1rem;
                }

                .features {
                    grid-template-columns: 1fr;
                }
            }

            @media (prefers-reduced-motion: reduce) {
                .cta-button {
                    transition: none;
                }
                .cta-button:hover {
                    transform: none;
                }
            }

            a {
                color: #667eea;
                text-decoration: none;
            }

            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <section class="hero">
                <div class="hero-content">
                    <h1>Verbo da Vida Braga</h1>
                    <p>Portal de Gestão Administrativa e Comunitária - Genesis.</p>
                    <p style="margin-bottom: 2.5rem; font-size: 0.95rem; color: #9ca3af;">Acesse a plataforma de gerenciamento interno para membros e administradores.</p>
                    <a href="/login" class="cta-button">Entrar no Genesis</a>
                </div>
                <div class="hero-visual">
                    <div class="hero-visual-content">
                        <div class="hero-visual-icon">🔐</div>
                        <div class="hero-visual-text">Acesso Seguro</div>
                    </div>
                </div>
            </section>

            <div style="padding: 0 3rem;">
                <div class="features">
                    <div class="feature">
                        <div class="feature-title">📊 Gestão Administrativa</div>
                        <div class="feature-description">Ferramentas completas para gerenciar processos e informações institucionais.</div>
                    </div>
                    <div class="feature">
                        <div class="feature-title">👥 Comunidade Integrada</div>
                        <div class="feature-description">Plataforma conectada para colaboradores e membros da comunidade.</div>
                    </div>
                    <div class="feature">
                        <div class="feature-title">⚡ Performance</div>
                        <div class="feature-description">Carregamento rápido e resposta instantânea em qualquer dispositivo.</div>
                    </div>
                </div>
            </div>

            <footer>
                <p>&copy; 2026 Verbo da Vida Braga. Todos os direitos reservados.</p>
                <p style="margin-top: 0.5rem; font-size: 0.8rem;">Genesis v1.0</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return html
