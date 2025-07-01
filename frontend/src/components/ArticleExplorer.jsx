// frontend/src/components/ArticleExplorer.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { FaSearch, FaFilter } from 'react-icons/fa';

/**
 * A component that allows users to browse articles with filters.
 * Users can filter by source, date, and search by keyword.
 * Today's date is selected by default, and articles are only shown when a date is selected.
 * Date selection is limited to the past 30 days to control request costs.
 * 
 * @returns {JSX.Element} The rendered article explorer
 */
function ArticleExplorer() {
    // State for articles fetched from the API
    const [articles, setArticles] = useState([]);
    // State for media sources (for the source filter)
    const [mediaSources, setMediaSources] = useState([]);
    // Filter states
    const [sourceFilter, setSourceFilter] = useState('');

    // Calculate date limits (today and 30 days ago)
    const today = new Date();
    const formattedToday = today.toISOString().split('T')[0]; // Format as YYYY-MM-DD

    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const formattedThirtyDaysAgo = thirtyDaysAgo.toISOString().split('T')[0];

    // Set today's date as default date filter
    const [dateFilter, setDateFilter] = useState(formattedToday);
    const [keywordFilter, setKeywordFilter] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const API_URL = 'http://localhost:8000';

    // Fetch media sources and articles on mount
    useEffect(() => {
        // Fetch media sources for the filter dropdown
        axios.get(`${API_URL}/media_sources`)
            .then(response => setMediaSources(response.data))
            .catch(error => console.error('Error fetching media sources:', error));

        // Initial articles fetch with today's date
        fetchArticles();
    }, []);

    /**
     * Fetches articles from the API based on current filters.
     */
    const fetchArticles = () => {
        // Only fetch if date is selected and within valid range
        if (!dateFilter || dateFilter > formattedToday || dateFilter < formattedThirtyDaysAgo) {
            setArticles([]);
            return;
        }

        setIsLoading(true);

        // Build query parameters
        const params = {};
        if (sourceFilter) params.source = sourceFilter;
        if (dateFilter) params.date = dateFilter;
        if (keywordFilter) params.keyword = keywordFilter;

        axios.get(`${API_URL}/articles`, { params })
            .then(response => {
                setArticles(response.data);
                setIsLoading(false);
            })
            .catch(error => {
                console.error('Error fetching articles:', error);
                setArticles([]);
                setIsLoading(false);
            });
    };

    /**
     * Handles source filter changes.
     * @param {Object} event - The select event
     */
    const handleSourceChange = (event) => {
        setSourceFilter(event.target.value);
        // Fetch articles immediately when source changes
        setTimeout(() => fetchArticles(), 0);
    };

    /**
     * Handles date filter changes.
     * @param {Object} event - The input event
     */
    const handleDateChange = (event) => {
        const selectedDate = event.target.value;

        // Validate date is within allowed range
        if (selectedDate > formattedToday) {
            alert("Cannot select future dates");
            return;
        }

        if (selectedDate < formattedThirtyDaysAgo) {
            alert("Cannot select dates more than 30 days in the past");
            return;
        }

        setDateFilter(selectedDate);
        // Fetch articles immediately when date changes
        setTimeout(() => fetchArticles(), 0);
    };

    /**
     * Handles keyword search input changes.
     * @param {Object} event - The input event
     */
    const handleKeywordChange = (event) => {
        setKeywordFilter(event.target.value);
    };

    /**
     * Handles keyword search form submission.
     * @param {Object} event - The form event
     */
    const handleKeywordSearch = (event) => {
        event.preventDefault();
        fetchArticles();
    };

    /**
     * Clears all filters and resets to defaults
     */
    const handleClearFilters = () => {
        setSourceFilter('');
        setDateFilter(formattedToday);
        setKeywordFilter('');
        setTimeout(() => fetchArticles(), 0);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-gray-800 rounded-lg shadow-lg p-6 min-h-[80vh]"
        >
            <h3 className="text-xl font-semibold mb-4 text-white flex items-center">
                <FaFilter className="mr-2" /> Article Explorer
            </h3>

            {/* Filters */}
            <div className="mb-4 flex flex-col md:flex-row gap-4">
                {/* Source Filter */}
                <div>
                    <label htmlFor="source-filter" className="block mb-2 text-gray-300">Source:</label>
                    <select
                        id="source-filter"
                        value={sourceFilter}
                        onChange={handleSourceChange}
                        className="w-full md:w-48 p-2 border rounded bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="">All Sources</option>
                        {mediaSources.map(source => (
                            <option key={source.source} value={source.source} className="bg-gray-700 text-white">
                                {source.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Date Filter */}
                <div>
                    <label htmlFor="date-filter" className="block mb-2 text-gray-300">Date:</label>
                    <input
                        type="date"
                        id="date-filter"
                        value={dateFilter}
                        onChange={handleDateChange}
                        min={formattedThirtyDaysAgo}
                        max={formattedToday}
                        className="w-full md:w-48 p-2 border rounded bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                </div>

                {/* Keyword Search */}
                <div className="flex-grow">
                    <label htmlFor="keyword-filter" className="block mb-2 text-gray-300">Keyword:</label>
                    <form onSubmit={handleKeywordSearch} className="flex">
                        <input
                            type="text"
                            id="keyword-filter"
                            value={keywordFilter}
                            onChange={handleKeywordChange}
                            placeholder="Search articles..."
                            className="flex-grow p-2 border rounded-l bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 text-white rounded-r hover:bg-blue-700 transition-colors"
                        >
                            <FaSearch />
                        </button>
                    </form>
                </div>
            </div>

            {/* Clear filters button */}
            <div className="mb-4">
                <button
                    onClick={handleClearFilters}
                    className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                >
                    Reset Filters
                </button>
            </div>

            {/* Loading indicator */}
            {isLoading && (
                <div className="flex justify-center my-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            )}

            {/* Articles list */}
            <div className="overflow-y-auto max-h-[60vh] pr-2 custom-scrollbar">
                {!isLoading && articles.length > 0 ? (
                    articles.map(article => (
                        <motion.div
                            key={article.id}
                            className="mb-4 p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.3 }}
                        >
                            <h4 className="text-lg font-semibold text-white mb-2">{article.raw_title}</h4>
                            <p className="text-gray-400 mb-2">
                                Source: {article.source_name} | Published: {new Date(article.publication_date).toLocaleString()}
                            </p>
                            <p className="text-gray-300 mb-4">
                                {article.clean_content?.substring(0, 150)}...
                            </p>
                            <a
                                href={article.link}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-400 hover:underline"
                            >
                                Read More
                            </a>
                        </motion.div>
                    ))
                ) : !isLoading && (
                    <p className="text-gray-400 text-center py-8">
                        {dateFilter ? "No articles found for the selected filters." : "Please select a date to view articles."}
                    </p>
                )}
            </div>
        </motion.div>
    );
}

export default ArticleExplorer;