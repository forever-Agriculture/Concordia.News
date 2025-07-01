// frontend/src/components/MediaSourceCard.jsx
import React from 'react';
import { FaGlobe, FaCalendarAlt, FaBuilding, FaInfoCircle } from 'react-icons/fa';

/**
 * A component that displays detailed information about a media source.
 * Fetches and renders all available fields from the media_sources table, including
 * basic metadata (name, country, logo), ownership details, founding information,
 * website, calculated bias, and third-party bias/reliability ratings from Ad Fontes,
 * AllSides, and Media Bias/Fact Check. Handles optional fields with 'N/A' fallbacks
 * and provides a fallback image if the logo fails to load.
 * 
 * @param {Object} props - Component props
 * @param {Object} props.mediaSource - The media source object from the database,
 *                                    conforming to the MediaSource Pydantic model
 * @returns {JSX.Element} The rendered media source card
 */
function MediaSourceCard({ mediaSource }) {
    // Destructure mediaSource to access all fields
    const {
        name, country, flag_emoji, logo_url, founded_year, website, description,
        owner, ownership_category, rationale_for_ownership, calculated_bias,
        calculated_bias_score, bias_confidence, last_updated,
        ad_fontes_bias, ad_fontes_reliability, ad_fontes_rating_url, ad_fontes_date_rated,
        allsides_bias, allsides_reliability, allsides_rating_url, allsides_date_rated,
        media_bias_fact_check_bias, media_bias_fact_check_reliability,
        media_bias_fact_check_rating_url, media_bias_fact_check_date_rated,
    } = mediaSource;

    // Fallback image if logo fails to load
    const handleImageError = (e) => {
        e.target.src = 'https://via.placeholder.com/64';
    };

    // Format date for display
    const formatDate = (date) => {
        return date ? new Date(date).toLocaleDateString() : 'N/A';
    };

    // Get color based on bias score
    const getBiasColor = (score) => {
        if (score === null) return 'gray';
        if (score <= -4) return 'red-700';
        if (score <= -2) return 'red-500';
        if (score < 0) return 'red-300';
        if (score === 0) return 'gray-500';
        if (score < 2) return 'blue-300';
        if (score < 4) return 'blue-500';
        return 'blue-700';
    };

    // Replace the dynamic class approach with a more reliable method
    const getBiasColorClass = (score) => {
        if (score === null) return "bg-gray-500";
        if (score <= -4) return "bg-red-700";
        if (score <= -2) return "bg-red-500";
        if (score < 0) return "bg-red-300";
        if (score === 0) return "bg-gray-500";
        if (score < 2) return "bg-blue-300";
        if (score < 4) return "bg-blue-500";
        return "bg-blue-700";
    };

    return (
        <div className="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
            {/* Header with logo and name */}
            <div className="p-6 bg-gradient-to-r from-gray-700 to-gray-800 border-b border-gray-700">
                <div className="flex items-center">
                    <div className="relative">
                        <img
                            src={logo_url}
                            alt={`${name} logo`}
                            className="w-16 h-16 rounded-full object-contain bg-white p-1 border-2 border-gray-600 shadow-md"
                            onError={handleImageError}
                        />
                        <span className="absolute bottom-0 right-0 text-lg">{flag_emoji}</span>
                    </div>
                    <div className="ml-4">
                        <h2 className="text-2xl font-bold">{name}</h2>
                        <p className="text-gray-400">{country}</p>
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="p-6">
                {/* Description */}
                <div className="mb-6">
                    <p className="text-gray-300 italic">
                        "{description || 'No description available'}"
                    </p>
                </div>

                {/* Quick facts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="flex items-start">
                        <FaBuilding className="text-gray-400 mt-1 mr-2" />
                        <div>
                            <h4 className="font-medium">Ownership</h4>
                            <p className="text-gray-300">{owner || 'N/A'}</p>
                            <p className="text-sm text-gray-400">{ownership_category || 'N/A'}</p>
                        </div>
                    </div>

                    <div className="flex items-start">
                        <FaCalendarAlt className="text-gray-400 mt-1 mr-2" />
                        <div>
                            <h4 className="font-medium">Founded</h4>
                            <p className="text-gray-300">{founded_year || 'N/A'}</p>
                        </div>
                    </div>

                    <div className="flex items-start">
                        <FaGlobe className="text-gray-400 mt-1 mr-2" />
                        <div>
                            <h4 className="font-medium">Website</h4>
                            <a
                                href={website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-400 hover:underline"
                            >
                                {website}
                            </a>
                        </div>
                    </div>

                    <div className="flex items-start">
                        <FaInfoCircle className="text-gray-400 mt-1 mr-2" />
                        <div>
                            <h4 className="font-medium">Last Updated</h4>
                            <p className="text-gray-300">{formatDate(last_updated)}</p>
                        </div>
                    </div>
                </div>

                {/* Bias section */}
                <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-4 pb-2 border-b border-gray-700">
                        Political Bias Analysis
                    </h3>

                    <div className="bg-gray-700 p-4 rounded-lg mb-4">
                        <div className="flex justify-between items-center mb-2">
                            <h4 className="font-medium">Calculated Bias</h4>
                            <span className={`px-3 py-1 rounded-full text-white ${getBiasColorClass(calculated_bias_score)}`}>
                                {calculated_bias || 'Unrated'}
                            </span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span>Score: {calculated_bias_score !== null ? calculated_bias_score.toFixed(2) : 'N/A'}</span>
                            <span>Confidence: {bias_confidence !== null ? (bias_confidence * 100).toFixed(0) + '%' : 'N/A'}</span>
                        </div>
                    </div>

                    {/* Third-party ratings */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-gray-700 p-3 rounded-lg">
                            <h4 className="font-medium mb-2">Ad Fontes Media</h4>
                            <p className="text-sm">Bias: <span className="font-medium">{ad_fontes_bias !== null ? ad_fontes_bias.toFixed(2) : 'N/A'}</span></p>
                            <p className="text-sm">Reliability: <span className="font-medium">{ad_fontes_reliability !== null ? ad_fontes_reliability.toFixed(2) : 'N/A'}</span></p>
                            <p className="text-sm mt-1">
                                {ad_fontes_rating_url && (
                                    <a href={ad_fontes_rating_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline text-xs">
                                        View Rating
                                    </a>
                                )}
                                {ad_fontes_date_rated && (
                                    <span className="text-xs text-gray-400 ml-2">
                                        ({formatDate(ad_fontes_date_rated)})
                                    </span>
                                )}
                            </p>
                        </div>

                        <div className="bg-gray-700 p-3 rounded-lg">
                            <h4 className="font-medium mb-2">AllSides</h4>
                            <p className="text-sm">Bias: <span className="font-medium">{allsides_bias !== null ? allsides_bias.toFixed(2) : 'N/A'}</span></p>
                            <p className="text-sm">Reliability: <span className="font-medium">{allsides_reliability !== null ? allsides_reliability.toFixed(2) : 'N/A'}</span></p>
                            <p className="text-sm mt-1">
                                {allsides_rating_url && (
                                    <a href={allsides_rating_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline text-xs">
                                        View Rating
                                    </a>
                                )}
                                {allsides_date_rated && (
                                    <span className="text-xs text-gray-400 ml-2">
                                        ({formatDate(allsides_date_rated)})
                                    </span>
                                )}
                            </p>
                        </div>

                        <div className="bg-gray-700 p-3 rounded-lg">
                            <h4 className="font-medium mb-2">Media Bias/Fact Check</h4>
                            <p className="text-sm">Bias: <span className="font-medium">{media_bias_fact_check_bias !== null ? media_bias_fact_check_bias.toFixed(2) : 'N/A'}</span></p>
                            <p className="text-sm">Reliability: <span className="font-medium">{media_bias_fact_check_reliability !== null ? media_bias_fact_check_reliability.toFixed(2) : 'N/A'}</span></p>
                            <p className="text-sm mt-1">
                                {media_bias_fact_check_rating_url && (
                                    <a href={media_bias_fact_check_rating_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline text-xs">
                                        View Rating
                                    </a>
                                )}
                                {media_bias_fact_check_date_rated && (
                                    <span className="text-xs text-gray-400 ml-2">
                                        ({formatDate(media_bias_fact_check_date_rated)})
                                    </span>
                                )}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Ownership rationale */}
                {rationale_for_ownership && (
                    <div className="mt-4 p-4 bg-gray-700 rounded-lg border-l-4 border-blue-500">
                        <h4 className="font-medium mb-1">Ownership Rationale</h4>
                        <p className="text-sm text-gray-300">{rationale_for_ownership}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default MediaSourceCard;