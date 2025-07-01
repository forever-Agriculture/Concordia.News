// Import environment config
import config from '../../config/environment';

// Create axios instance with environment-aware base URL
import axios from 'axios';

const apiClient = axios.create({
    baseURL: config.api.baseUrl,
    headers: {
        'Content-Type': 'application/json'
    }
});

// API functions
export const getMediaSources = () => apiClient.get(config.api.endpoints.mediaSources);
export const getArticles = (params) => apiClient.get(config.api.endpoints.articles, { params });
export const getAnalyses = (params) => apiClient.get(config.api.endpoints.analyses, { params });
export const getHealth = () => apiClient.get(config.api.endpoints.health);

export default apiClient; 