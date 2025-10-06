class GenerationSplash {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container element with id '${containerId}' not found`);
        }
        
        this.options = {
            labelCount: options.labelCount || 0,
            templateType: options.templateType || 'Horizontal',
            ...options
        };
        
        this.isRunning = false;
        this.generationProgress = 0;
        this.statusTextIndex = 0;
        this.statusTextInterval = null;
        
        this.init();
    }
    
    init() {
        try {
            // Create the splash HTML structure
            this.createSplashHTML();
            
            // Start animations
            this.isRunning = true;
            this.startStatusTextAnimation();
        } catch (error) {
            console.error('Error initializing GenerationSplash:', error);
            throw error;
        }
    }
    
    createSplashHTML() {
        this.container.innerHTML = `
            <div class="background-pattern"></div>
            
            <div id="generation-splash-container">
                <div class="splash-content">
                    <div class="logo-container">
                        <div class="logo-icon">
                            <svg width="80" height="80" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <!-- Clipboard with rainbow gradient border -->
                                <defs>
                                    <linearGradient id="genSplashClipboardGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" style="stop-color:#ff0000;stop-opacity:1" />
                                        <stop offset="16.67%" style="stop-color:#ff8000;stop-opacity:1" />
                                        <stop offset="33.33%" style="stop-color:#ffff00;stop-opacity:1" />
                                        <stop offset="50%" style="stop-color:#00ff00;stop-opacity:1" />
                                        <stop offset="66.67%" style="stop-color:#0080ff;stop-opacity:1" />
                                        <stop offset="83.33%" style="stop-color:#8000ff;stop-opacity:1" />
                                        <stop offset="100%" style="stop-color:#ff0080;stop-opacity:1" />
                                    </linearGradient>
                                </defs>
                                
                                <!-- Clipboard background -->
                                <rect x="4" y="8" width="40" height="36" rx="6" fill="url(#genSplashClipboardGradient)" stroke="url(#genSplashClipboardGradient)" stroke-width="2"/>
                                <rect x="6" y="10" width="36" height="32" rx="4" fill="white"/>
                                
                                <!-- Metallic clip -->
                                <rect x="16" y="4" width="16" height="8" rx="4" fill="#c0c0c0"/>
                                <rect x="18" y="6" width="12" height="4" rx="2" fill="#e0e0e0"/>
                                <rect x="20" y="2" width="8" height="6" rx="3" fill="#a0a0a0"/>
                                
                                <!-- Paper -->
                                <rect x="8" y="12" width="32" height="28" rx="2" fill="white" stroke="#e0e0e0" stroke-width="0.5"/>
                                
                                <!-- Cannabis leaf -->
                                <g transform="translate(24, 28)">
                                    <!-- Main leaf shape -->
                                    <path d="M0,-8 C-2,-6 -3,-3 -3,0 C-3,3 -2,6 0,8 C2,6 3,3 3,0 C3,-3 2,-6 0,-8 Z" fill="#228B22"/>
                                    
                                    <!-- Leaf serrations -->
                                    <path d="M-2.5,-6 L-2,-5.5 L-1.5,-6 L-2,-6.5 Z" fill="#228B22"/>
                                    <path d="M-1.5,-4 L-1,-3.5 L-0.5,-4 L-1,-4.5 Z" fill="#228B22"/>
                                    <path d="M-1,-2 L-0.5,-1.5 L0,-2 L-0.5,-2.5 Z" fill="#228B22"/>
                                    <path d="M-0.5,0 L0,0.5 L0.5,0 L0,-0.5 Z" fill="#228B22"/>
                                    <path d="M-1,2 L-0.5,2.5 L0,2 L-0.5,1.5 Z" fill="#228B22"/>
                                    <path d="M-1.5,4 L-1,4.5 L-0.5,4 L-1,3.5 Z" fill="#228B22"/>
                                    <path d="M-2.5,6 L-2,6.5 L-1.5,6 L-2,5.5 Z" fill="#228B22"/>
                                    
                                    <path d="M2.5,-6 L2,-5.5 L1.5,-6 L2,-6.5 Z" fill="#228B22"/>
                                    <path d="M1.5,-4 L1,-3.5 L0.5,-4 L1,-4.5 Z" fill="#228B22"/>
                                    <path d="M1,-2 L0.5,-1.5 L0,-2 L0.5,-2.5 Z" fill="#228B22"/>
                                    <path d="M0.5,0 L0,0.5 L-0.5,0 L0,-0.5 Z" fill="#228B22"/>
                                    <path d="M1,2 L0.5,2.5 L0,2 L0.5,1.5 Z" fill="#228B22"/>
                                    <path d="M1.5,4 L1,4.5 L0.5,4 L1,3.5 Z" fill="#228B22"/>
                                    <path d="M2.5,6 L2,6.5 L1.5,6 L2,5.5 Z" fill="#228B22"/>
                                    
                                    <!-- Center vein -->
                                    <line x1="0" y1="-8" x2="0" y2="8" stroke="#006400" stroke-width="0.5"/>
                                </g>
                            </svg>
                        </div>
                    </div>
                    
                    <h1 class="app-title">AGT DESIGNER</h1>
                    <p class="app-subtitle">AUTO-GENERATING TAG DESIGNER</p>
                    
                    <div class="loading-container">
                        <div class="loading-bar">
                            <div class="loading-progress"></div>
                        </div>
                        <div class="loading-text">Processing your request...</div>
                    </div>
                    
                    <div class="loading-dots">
                        <div class="dot"></div>
                        <div class="dot"></div>
                        <div class="dot"></div>
                    </div>
                    
                    <!-- Copyright text matching title card -->
                    <p class="copyright-text">©2025 Created by Adam Cordova for A Greener Today</p>
                    
                    <div class="features">
                        <div class="feature">
                            <div class="feature-icon">⚡</div>
                            <div class="feature-text">Fast</div>
                        </div>
                        <div class="feature">
                            <div class="feature-icon">🎯</div>
                            <div class="feature-text">Precise</div>
                        </div>
                        <div class="feature">
                            <div class="feature-icon">🛡️</div>
                            <div class="feature-text">Reliable</div>
                        </div>
                    </div>
                </div>
                
                <div class="version-badge">v2.0.0</div>
                <div class="status-indicator">
                    <div class="status-dot"></div>
                    <span>Processing</span>
                </div>
                <button id="exitGenerationBtn" onclick="window.generationSplash && window.generationSplash.hide()" style="position: absolute; bottom: 15px; right: 15px; background: rgba(220, 53, 69, 0.8); border: 1px solid rgba(220, 53, 69, 0.8); color: white; padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);" onmouseover="this.style.background='rgba(220, 53, 69, 1)'; this.style.transform='scale(1.05)'" onmouseout="this.style.background='rgba(220, 53, 69, 0.8)'; this.style.transform='scale(1)'">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px;">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                    Exit
                </button>
            </div>
        `;
        
        // Add CSS styles
        this.addStyles();
        
        // Add interactive effects like the opening splash
        this.addInteractiveEffects();
    }
    
    addStyles() {
        const styleId = 'generation-splash-styles';
        if (document.getElementById(styleId)) {
            return; // Styles already added
        }
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .generation-splash-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            }
            
            .generation-splash-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            .background-pattern {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                opacity: 0.1;
                background-image: 
                    radial-gradient(circle at 20% 80%, #00d4aa 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, #00d4aa 0%, transparent 50%),
                    radial-gradient(circle at 40% 40%, #00d4aa 0%, transparent 50%);
                animation: background-shift 8s ease-in-out infinite;
            }
            
            @keyframes background-shift {
                0%, 100% { transform: scale(1) rotate(0deg); }
                50% { transform: scale(1.1) rotate(180deg); }
            }
            
            #generation-splash-container {
                position: relative;
                width: 600px;
                height: 400px;
                border-radius: 24px;
                overflow: hidden;
                background: rgba(22, 33, 62, 0.95);
                border: 1px solid rgba(0, 212, 170, 0.2);
                box-shadow: 
                    0 20px 40px rgba(0, 0, 0, 0.3),
                    0 0 0 1px rgba(0, 212, 170, 0.1);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                z-index: 2;
                transform: translateX(0);
            }
            
            .splash-content {
                position: relative;
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 60px;
                color: white;
                text-align: center;
            }
            
            .logo-container {
                position: relative;
                margin-bottom: 30px;
            }
            
            .logo-icon {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #00d4aa, #0099cc);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 36px;
                box-shadow: 
                    0 15px 35px rgba(0, 212, 170, 0.3),
                    0 0 0 1px rgba(0, 212, 170, 0.2);
                animation: logo-float 3s ease-in-out infinite;
                position: relative;
            }
            
            .logo-icon::before {
                content: '';
                position: absolute;
                top: -2px;
                left: -2px;
                right: -2px;
                bottom: -2px;
                background: linear-gradient(45deg, #00d4aa, #0099cc, #00d4aa);
                border-radius: 22px;
                z-index: -1;
                animation: logo-glow 2s ease-in-out infinite alternate;
            }
            
            @keyframes logo-float {
                0%, 100% { 
                    transform: translateY(0px) scale(1);
                }
                50% { 
                    transform: translateY(-8px) scale(1.02);
                }
            }
            
            @keyframes logo-glow {
                0% { opacity: 0.6; }
                100% { opacity: 1; }
            }
            
            .app-title {
                color: #fff !important;
                background: none !important;
                -webkit-background-clip: initial !important;
                -webkit-text-fill-color: initial !important;
                background-clip: initial !important;
                font-weight: 900;
                letter-spacing: 3px;
                font-size: 3.5rem;
                margin-bottom: 12px;
                text-shadow: 
                    0 4px 12px rgba(0,0,0,0.5),
                    0 6px 20px rgba(0,0,0,0.4),
                    0 2px 4px rgba(160,132,232,0.4),
                    0 0 30px rgba(160,132,232,0.3);
                filter: drop-shadow(0 6px 12px rgba(0,0,0,0.4));
                position: relative;
                line-height: 1.1;
                text-align: center !important;
                width: 100%;
            }
            
            .app-subtitle {
                color: #fff !important;
                background: none !important;
                -webkit-background-clip: initial !important;
                -webkit-text-fill-color: initial !important;
                background-clip: initial !important;
                font-size: 1.5rem;
                font-weight: 700;
                letter-spacing: 2px;
                text-align: center !important;
                width: 100%;
                opacity: 1;
                text-transform: uppercase;
                text-shadow: 
                    0 3px 8px rgba(0,0,0,0.5),
                    0 4px 16px rgba(0,0,0,0.4),
                    0 2px 4px rgba(139,92,246,0.4),
                    0 0 20px rgba(139,92,246,0.3);
                filter: drop-shadow(0 3px 6px rgba(0,0,0,0.4));
                margin-bottom: 20px;
                line-height: 1.2;
            }
            
            .copyright-text {
                font-size: 1.1rem;
                color: rgba(255, 255, 255, 0.8);
                margin-top: 0.5rem;
                font-weight: 500;
                letter-spacing: 1px;
                text-align: center;
                text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5), 0 1px 2px rgba(160,132,232,0.3);
                opacity: 0.9;
                margin-bottom: 20px;
            }
            
            .loading-container {
                width: 100%;
                max-width: 400px;
                margin-bottom: 30px;
            }
            
            .loading-bar {
                width: 100%;
                height: 6px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                overflow: hidden;
                margin-bottom: 20px;
                position: relative;
            }
            
            .loading-progress {
                height: 100%;
                background: linear-gradient(90deg, #00d4aa, #0099cc, #00d4aa);
                border-radius: 3px;
                animation: loading-animation 3s ease-in-out infinite;
                position: relative;
            }
            
            .loading-progress::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
                animation: shimmer 2s ease-in-out infinite;
            }
            
            @keyframes loading-animation {
                0% { width: 0%; }
                50% { width: 100%; }
                100% { width: 0%; }
            }
            
            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            
            .loading-text {
                font-size: 16px;
                font-weight: 500;
                opacity: 0.8;
                margin-bottom: 25px;
                transition: opacity 0.3s ease;
            }
            
            .loading-dots {
                display: flex;
                gap: 8px;
                justify-content: center;
                margin-bottom: 25px;
            }
            
            .dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: rgba(0, 212, 170, 0.6);
                animation: dot-pulse 1.6s ease-in-out infinite both;
            }
            
            .dot:nth-child(1) { animation-delay: -0.32s; }
            .dot:nth-child(2) { animation-delay: -0.16s; }
            .dot:nth-child(3) { animation-delay: 0s; }
            
            @keyframes dot-pulse {
                0%, 80%, 100% {
                    transform: scale(0.8);
                    opacity: 0.4;
                }
                40% {
                    transform: scale(1.2);
                    opacity: 1;
                }
            }
            
            .version-badge {
                position: absolute;
                top: 20px;
                right: 20px;
                background: rgba(0, 212, 170, 0.15);
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border: 1px solid rgba(0, 212, 170, 0.2);
                color: #00d4aa;
            }
            
            .status-indicator {
                position: absolute;
                top: 20px;
                left: 20px;
                display: flex;
                align-items: center;
                gap: 6px;
                background: rgba(0, 212, 170, 0.15);
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border: 1px solid rgba(0, 212, 170, 0.2);
                color: #00d4aa;
            }
            
            .status-dot {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #00d4aa;
                animation: status-pulse 2s ease-in-out infinite;
            }
            
            @keyframes status-pulse {
                0%, 100% { opacity: 0.5; }
                50% { opacity: 1; }
            }
            
            .features {
                display: flex;
                gap: 25px;
                margin-top: 15px;
            }
            
            .feature {
                text-align: center;
                opacity: 0.6;
            }
            
            .feature-icon {
                font-size: 20px;
                margin-bottom: 6px;
            }
            
            .feature-text {
                font-size: 11px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            @media (max-width: 1200px) {
                #generation-splash-container {
                    transform: translateX(0);
                    width: 90vw;
                    max-width: 600px;
                }
            }
            
            @media (max-width: 900px) {
                #generation-splash-container {
                    transform: translateX(0);
                    width: 90vw;
                    max-width: 500px;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    addInteractiveEffects() {
        // Add subtle interactive effects like the opening splash
        document.addEventListener('mousemove', (e) => {
            const container = document.getElementById('generation-splash-container');
            if (!container) return;
            
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 30;
            const rotateY = (centerX - x) / 30;
            
            container.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });
        
        document.addEventListener('mouseleave', () => {
            const container = document.getElementById('generation-splash-container');
            if (container) {
                container.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
            }
        });
    }
    
    startStatusTextAnimation() {
        const statusTexts = [
            'Initializing generation...',
            'Loading templates...',
            'Processing data...',
            'Generating labels...',
            'Applying formatting...',
            'Finalizing document...',
            'Almost complete...'
        ];
        
        const statusTextElement = this.container.querySelector('.loading-text');
        if (!statusTextElement) return;
        
        this.statusTextInterval = setInterval(() => {
            statusTextElement.style.opacity = '0';
            setTimeout(() => {
                statusTextElement.textContent = statusTexts[this.statusTextIndex];
                statusTextElement.style.opacity = '1';
                this.statusTextIndex = (this.statusTextIndex + 1) % statusTexts.length;
            }, 300);
        }, 1200);
    }
    
    // Method to start animation
    start() {
        this.isRunning = true;
        this.startStatusTextAnimation();
    }
    
    // Method to stop animation
    stop() {
        this.isRunning = false;
        if (this.statusTextInterval) {
            clearInterval(this.statusTextInterval);
            this.statusTextInterval = null;
        }
    }
    
    // Method to hide splash screen
    hide() {
        this.stop();
        if (this.container) {
            this.container.style.display = 'none';
        }
    }
    
    // Method to show splash screen
    show() {
        if (this.container) {
            this.container.style.display = 'flex';
        }
        if (!this.isRunning) {
            this.start();
        }
    }
    
    // Method to update generation progress
    updateProgress(progress) {
        this.generationProgress = progress;
        // Update progress bar if needed
        const progressFill = this.container.querySelector('.loading-progress');
        if (progressFill && progress >= 0 && progress <= 100) {
            progressFill.style.width = `${progress}%`;
        }
    }
    
    // Method to update status text
    updateStatusText(text) {
        const statusTextElement = this.container.querySelector('.loading-text');
        if (statusTextElement) {
            statusTextElement.textContent = text;
        }
    }
}

// Auto-initialize if container exists
// DISABLED: This conflicts with the new canvas-based splash system in main.js
// The new system uses showEnhancedGenerationSplash() which expects a canvas element
// that gets removed when this old system initializes
/*
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('generationSplashModal');
    if (container) {
        try {
            // Get parameters from URL
            const urlParams = new URLSearchParams(window.location.search);
            const labelCount = urlParams.get('count') || '0';
            const templateType = urlParams.get('template') || 'Horizontal';
            
            window.generationSplash = new GenerationSplash('generationSplashModal', {
                labelCount: parseInt(labelCount),
                templateType: templateType
            });
        } catch (error) {
            console.error('Failed to initialize generation splash:', error);
            // Trigger fallback in the main script
            if (typeof showFallback === 'function') {
                showFallback();
            }
        }
    }
});
*/

window.GenerationSplash = GenerationSplash; 