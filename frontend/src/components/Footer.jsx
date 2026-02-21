import './Footer.css'

export default function Footer() {
    return (
        <footer className="footer">
            <div className="container footer-inner">
                <div className="footer-brand">
                    <span className="brand-icon">◆</span>
                    <span className="brand-text">VIL</span>
                    <p className="footer-desc">
                        Victor Institutional Logic — Institutional-grade trading intelligence powered by multi-layered analysis and AI.
                    </p>
                </div>

                <div className="footer-links">
                    <div className="footer-col">
                        <h4>Platform</h4>
                        <a href="#quotes">Live Quotes</a>
                        <a href="#calendar">Economic Calendar</a>
                        <a href="#news">Market News</a>
                        <a href="#tools">Trading Tools</a>
                    </div>
                    <div className="footer-col">
                        <h4>Resources</h4>
                        <a href="#">API Docs</a>
                        <a href="#">Knowledge Base</a>
                        <a href="#">Signal Methodology</a>
                    </div>
                    <div className="footer-col">
                        <h4>Legal</h4>
                        <a href="#">Risk Disclaimer</a>
                        <a href="#">Terms of Service</a>
                        <a href="#">Privacy Policy</a>
                    </div>
                </div>

                <div className="footer-bottom">
                    <p>© {new Date().getFullYear()} Victor Institutional Logic. All rights reserved.</p>
                    <p className="footer-disclaimer">
                        Trading involves risk. Past performance is not indicative of future results.
                    </p>
                </div>
            </div>
        </footer>
    )
}
