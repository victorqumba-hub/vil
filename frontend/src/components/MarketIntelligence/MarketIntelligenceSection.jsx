import MarketIntelligenceWidget from './MarketIntelligenceWidget'
import QuickConverter from './QuickConverter'
import FeaturedNewsSection from './FeaturedNewsSection'
import InterestRates from './InterestRates'
import MarketSentiment from './MarketSentiment'
import LiveMarketStrip from './LiveMarketStrip'
import './MarketIntelligence.css'

export default function MarketIntelligenceSection() {
    return (
        <section className="market-intel-section container">
            <div className="mi-top-grid">
                <div className="mi-left-col">
                    <MarketIntelligenceWidget />
                    <div className="mt-4">
                        <FeaturedNewsSection />
                    </div>
                </div>

                <div className="mi-right-col">
                    <QuickConverter />
                    <div className="mt-4">
                        <InterestRates />
                        <MarketSentiment />
                    </div>
                </div>
            </div>

            <div className="mi-bottom-strip mt-5">
                <LiveMarketStrip />
            </div>
        </section>
    )
}
