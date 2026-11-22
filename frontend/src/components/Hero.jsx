export default function Hero({ productCount, categoryCount }) {
  return (
    <section className="hero">
      <div className="container hero-inner">
        <div>
          <p className="hero-kicker">Spring Boot · Kafka · Elasticsearch · Redis · Spring Cloud</p>
          <h1>
            Shop smarter.
            <br />
            <span>Powered by microservices.</span>
          </h1>
          <p className="hero-sub">
            A distributed e-commerce demo — every service owns its data and talks through a
            single API gateway.
          </p>
          <div className="hero-stats">
            <div>
              <strong>{productCount}</strong>
              <span>Products</span>
            </div>
            <div>
              <strong>{categoryCount}</strong>
              <span>Categories</span>
            </div>
            <div>
              <strong>5</strong>
              <span>Microservices</span>
            </div>
          </div>
        </div>

        <div className="hero-art" aria-hidden="true">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
          <div className="hero-card">
            <span className="pulse" />
            <span>api-gateway online</span>
          </div>
        </div>
      </div>
    </section>
  )
}
