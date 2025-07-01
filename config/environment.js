/**
 * Global environment configuration
 * Toggle between 'development' and 'production' to switch environments
 */

const ENV = 'production'; // Change to 'production' for production mode

// Derived configuration values based on environment
const config = {
    // Core environment
    environment: ENV,
    isProduction: ENV === 'production',
    isDevelopment: ENV === 'development',

    // API endpoints
    api: {
        baseUrl: ENV === 'development'
            ? 'http://localhost:8000'
            : '/api',
        endpoints: {
            mediaSources: '/media_sources',
            articles: '/articles',
            analyses: '/analyses',
            health: '/health'
        }
    },

    // Frontend settings
    frontend: {
        port: ENV === 'development' ? 3000 : 8080,
        baseUrl: ENV === 'development'
            ? 'http://localhost:3000'
            : 'https://concordia.news'
    },

    // Docker compose settings
    docker: {
        composeFile: ENV === 'development'
            ? 'docker-compose.yml'
            : 'docker-compose.yml -f docker-compose.prod.yml'
    },

    // Database connection
    database: {
        path: '/app/news_analysis.db',
        backupEnabled: ENV === 'production'
    },

    // Logging settings
    logging: {
        level: ENV === 'development' ? 'debug' : 'info',
        directory: '/app/logs'
    }
};

// For Node.js environments
if (typeof module !== 'undefined') {
    module.exports = config;
}

// For ES modules (frontend)
export default config; 