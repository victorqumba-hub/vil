import './GlassCard.css'

export default function GlassCard({ title, icon, children, className = '' }) {
    return (
        <div className={`glass-card gc-wrapper ${className}`}>
            {(title || icon) && (
                <div className="gc-header">
                    {icon && <span className="gc-icon">{icon}</span>}
                    {title && <h3 className="gc-title">{title}</h3>}
                </div>
            )}
            <div className="gc-body">{children}</div>
        </div>
    )
}
