// frontend/src/components/PoliticalSpectrum.jsx
import React, { useState } from 'react';

/**
 * A component that displays a political spectrum with media sources positioned based on their calculated bias.
 * Allows users to select a source, triggering the `onSelectSource` callback.
 * 
 * @param {Object} props - Component props
 * @param {Array} props.mediaSources - Array of media source objects from the database
 * @param {Function} props.onSelectSource - Callback function to handle source selection
 * @returns {JSX.Element} The rendered political spectrum
 */
function PoliticalSpectrum({ mediaSources, onSelectSource }) {
    // Track which source is being hovered
    const [hoveredSource, setHoveredSource] = useState(null);

    // Define bias range for positioning (-5 to +5)
    const biasRange = { min: -5, max: 5 };

    /**
     * Maps a bias score to a position on the spectrum
     * @param {number} biasScore - Bias score from -5 to +5
     * @returns {number} Percentage position (0-100)
     */
    const getBiasPosition = (biasScore) => {
        // Default to center if no bias
        if (biasScore === null || isNaN(biasScore)) return 50;

        // Map from -5...+5 to 0...100
        return ((biasScore - biasRange.min) / (biasRange.max - biasRange.min)) * 100;
    };

    // Define label positions with specific bias values based on media_rating_scales.md
    const labels = [
        { name: 'Far Left', bias: -5 },
        { name: 'Left', bias: -4 },
        { name: 'Center-Left', bias: -3 },
        { name: 'Lean Left', bias: -2 },
        { name: 'Slight Left', bias: -1 },
        { name: 'Neutral', bias: 0 },
        { name: 'Slight Right', bias: 1 },
        { name: 'Lean Right', bias: 2 },
        { name: 'Center-Right', bias: 3 },
        { name: 'Right', bias: 4 },
        { name: 'Far Right', bias: 5 },
    ];

    return (
        <div className="w-full py-16 px-4">
            <div className="w-full mx-auto">
                {/* Spectrum bar with labels */}
                <div className="relative mb-28">
                    {/* Position labels directly above their positions */}
                    {labels.map((label) => (
                        <div
                            key={label.name}
                            className="absolute text-center font-medium text-gray-500 dark:text-gray-300 transform -translate-x-1/2"
                            style={{
                                left: `${getBiasPosition(label.bias)}%`,
                                top: '-28px',
                                fontSize: '0.9rem',
                                width: '100px' // Fixed width for all labels
                            }}
                        >
                            {label.name}
                        </div>
                    ))}

                    {/* Spectrum gradient bar */}
                    <div className="h-5 w-full bg-gradient-to-r from-red-500 via-gray-300 to-blue-500 rounded-full shadow-md"></div>

                    {/* Tick marks for each label position */}
                    {labels.map((label) => (
                        <div
                            key={`tick-${label.name}`}
                            className="absolute w-0.5 h-6 bg-gray-400 dark:bg-gray-600 transform -translate-x-1/2"
                            style={{
                                left: `${getBiasPosition(label.bias)}%`,
                                top: '20px'
                            }}
                        />
                    ))}
                </div>

                {/* Media sources */}
                <div className="relative h-40"> {/* Reduced height since we're removing the names */}
                    {mediaSources.map((source, index) => {
                        const biasScore = source.calculated_bias_score || 0;
                        const position = getBiasPosition(biasScore);

                        // Calculate row based on index to prevent overlapping
                        // Use more rows if needed based on source count
                        const row = index % 2;
                        const topPosition = row === 0 ? '0px' : '70px'; // Reduced spacing between rows

                        // Determine if this source is being hovered
                        const isHovered = hoveredSource === source.source;

                        return (
                            <div
                                key={source.source}
                                className={`absolute transform -translate-x-1/2 cursor-pointer transition-all duration-300 ${isHovered ? 'scale-110' : ''}`}
                                style={{
                                    left: `${position}%`,
                                    top: topPosition,
                                    zIndex: isHovered ? 50 : 10, // Higher z-index when hovered
                                }}
                                onClick={() => onSelectSource(source)}
                                onMouseEnter={() => setHoveredSource(source.source)}
                                onMouseLeave={() => setHoveredSource(null)}
                                title={source.name} // Add title for tooltip on hover
                            >
                                <div className="relative">
                                    <img
                                        src={source.logo_url}
                                        alt={`${source.name} logo`}
                                        className={`w-16 h-16 rounded-full object-contain bg-white p-1 border-2 border-gray-200 dark:border-gray-700 ${isHovered ? 'shadow-xl' : 'shadow-lg'} transition-shadow`}
                                        onError={(e) => { e.target.src = 'https://via.placeholder.com/64?text=' + source.name.charAt(0) }}
                                    />
                                    <span className="absolute -top-2 -right-2 bg-gray-800 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center font-bold">
                                        {biasScore.toFixed(1)}
                                    </span>
                                </div>
                                {/* Removed the name span */}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

export default PoliticalSpectrum;