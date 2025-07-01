// frontend/src/components/AnalysisView.jsx
import React, { useState, useEffect } from 'react';

/**
 * A component that displays comprehensive analysis data for a selected media source.
 * Shows narratives, sentiment, bias, and promoted values from the analyses table.
 * Only allows selection of analyses from the last 8 days to reduce request load.
 * 
 * @param {Object} props - Component props
 * @param {Array} props.analyses - Array of analysis objects from the database
 * @returns {JSX.Element} The rendered analysis view
 */
function AnalysisView({ analyses }) {
    // Sort analyses by date (newest first)
    const sortedAnalyses = analyses.sort((a, b) => new Date(b.analysis_date) - new Date(a.analysis_date));

    // Filter to only include analyses from the last 8 days
    const eightDaysAgo = new Date();
    eightDaysAgo.setDate(eightDaysAgo.getDate() - 8);

    const recentAnalyses = sortedAnalyses.filter(analysis => {
        const analysisDate = new Date(analysis.analysis_date);
        return analysisDate >= eightDaysAgo;
    });

    const latestAnalysis = recentAnalyses.length > 0 ? recentAnalyses[0] : null;
    const [selectedAnalysis, setSelectedAnalysis] = useState(null);

    // Update selectedAnalysis when analyses change or when latestAnalysis changes
    useEffect(() => {
        setSelectedAnalysis(latestAnalysis);
    }, [latestAnalysis]);

    const handleDateChange = (event) => {
        const selected = recentAnalyses.find(a => a.analysis_date === event.target.value);
        setSelectedAnalysis(selected || latestAnalysis);
    };

    if (!latestAnalysis) {
        return (
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full">
                <h3 className="text-2xl font-bold mb-4 text-white">
                    Analysis
                </h3>
                <div className="p-6 text-center text-gray-400">
                    No analyses available for this source in the last 8 days.
                </div>
            </div>
        );
    }

    // Helper function to render narrative sections
    const getCoverageColorClass = (coverage) => {
        if (coverage >= 30) return "bg-blue-900 text-blue-100";
        if (coverage >= 20) return "bg-green-900 text-green-100";
        if (coverage >= 10) return "bg-yellow-900 text-yellow-100";
        return "bg-gray-700 text-gray-300";
    };

    const renderNarrativeSection = (theme, coverage, examples, index) => {
        if (!theme) return null;
        const coverageColorClass = getCoverageColorClass(coverage);

        return (
            <div key={index} className="mb-4 p-4 bg-gray-700 rounded-lg shadow">
                <div className="flex justify-between items-center mb-2">
                    <h5 className="font-bold text-lg">{theme}</h5>
                    <span className={`px-2 py-1 rounded-full text-sm font-medium ${coverageColorClass}`}>
                        {coverage}%
                    </span>
                </div>
                <p className="text-sm text-gray-300">{examples}</p>
            </div>
        );
    };

    return (
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg w-full">
            <h3 className="text-2xl font-bold mb-4 text-white">
                Analysis for {selectedAnalysis?.source_name}
            </h3>

            <div className="mb-6">
                <label htmlFor="analysis-date" className="block mb-2 font-medium">Select Analysis Date:</label>
                <select
                    id="analysis-date"
                    value={selectedAnalysis?.analysis_date || ""}
                    onChange={handleDateChange}
                    className="w-full p-2 border rounded bg-gray-700 text-white border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {recentAnalyses.map(analysis => (
                        <option key={analysis.id} value={analysis.analysis_date} className="bg-gray-700 text-white">
                            {analysis.analysis_date}
                        </option>
                    ))}
                </select>
            </div>

            {selectedAnalysis && (
                <div className="space-y-6">
                    {/* Basic Information */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div className="p-4 bg-gray-700 rounded-lg shadow">
                            <h4 className="font-semibold mb-2 text-gray-200">Date</h4>
                            <p>{selectedAnalysis.analysis_date}</p>
                        </div>
                        <div className="p-4 bg-gray-700 rounded-lg shadow">
                            <h4 className="font-semibold mb-2 text-gray-200">Articles Analyzed</h4>
                            <p>{selectedAnalysis.numbers_of_articles}</p>
                        </div>
                    </div>

                    {/* Political Bias */}
                    <div className="mb-6">
                        <h4 className="text-xl font-semibold mb-4 text-white">Political Bias</h4>
                        <div className="p-4 bg-gray-700 rounded-lg shadow">
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <span className="text-xl font-bold">{selectedAnalysis.bias_political_leaning}</span>
                                    <span className="ml-2 text-sm text-gray-300">
                                        (Score: {selectedAnalysis.bias_political_score.toFixed(1)})
                                    </span>
                                </div>
                                <div className="text-sm">
                                    <span className="font-medium">Confidence: </span>
                                    <span>{(selectedAnalysis.bias_confidence * 100).toFixed(0)}%</span>
                                </div>
                            </div>

                            {/* Bias visualization */}
                            <div className="relative h-6 bg-gradient-to-r from-red-500 via-gray-300 to-blue-500 rounded-full mb-2">
                                <div
                                    className="absolute w-4 h-8 bg-white top-1/2 transform -translate-y-1/2 -translate-x-1/2 rounded-full shadow-md"
                                    style={{
                                        left: `${((selectedAnalysis.bias_political_score + 5) / 10) * 100}%`
                                    }}
                                ></div>
                            </div>
                            <div className="flex justify-between text-xs text-gray-300">
                                <span>Far Left</span>
                                <span>Neutral</span>
                                <span>Far Right</span>
                            </div>

                            {selectedAnalysis.bias_supporting_evidence && (
                                <div className="mt-4">
                                    <h5 className="font-semibold mb-2">Supporting Evidence:</h5>
                                    <p className="text-sm text-gray-300">
                                        {selectedAnalysis.bias_supporting_evidence}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Sentiment Analysis */}
                    <div className="mb-6">
                        <h4 className="text-xl font-semibold mb-4 text-white">Sentiment Analysis</h4>
                        <div className="p-4 bg-gray-700 rounded-lg shadow">
                            <div className="flex flex-wrap gap-4 justify-between">
                                <div className="text-center">
                                    <div className="text-green-500 text-2xl font-bold">
                                        {selectedAnalysis.sentiment_positive_percentage}%
                                    </div>
                                    <div className="text-sm text-gray-300">Positive</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-gray-400 text-2xl font-bold">
                                        {selectedAnalysis.sentiment_neutral_percentage}%
                                    </div>
                                    <div className="text-sm text-gray-300">Neutral</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-red-500 text-2xl font-bold">
                                        {selectedAnalysis.sentiment_negative_percentage}%
                                    </div>
                                    <div className="text-sm text-gray-300">Negative</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-blue-500 text-2xl font-bold">
                                        {(selectedAnalysis.sentiment_confidence * 100).toFixed(0)}%
                                    </div>
                                    <div className="text-sm text-gray-300">Confidence</div>
                                </div>
                            </div>

                            {/* Sentiment visualization */}
                            <div className="relative h-6 rounded-full overflow-hidden mt-4">
                                <div className="absolute inset-0 flex">
                                    <div
                                        className="bg-green-500 h-full flex items-center justify-center text-xs text-white font-medium"
                                        style={{ width: `${selectedAnalysis.sentiment_positive_percentage}%` }}
                                    >
                                        {selectedAnalysis.sentiment_positive_percentage > 5 ? `Positive ${selectedAnalysis.sentiment_positive_percentage}%` : ''}
                                    </div>
                                    <div
                                        className="bg-gray-500 h-full flex items-center justify-center text-xs text-white font-medium"
                                        style={{ width: `${selectedAnalysis.sentiment_neutral_percentage}%` }}
                                    >
                                        {selectedAnalysis.sentiment_neutral_percentage > 5 ? `Neutral ${selectedAnalysis.sentiment_neutral_percentage}%` : ''}
                                    </div>
                                    <div
                                        className="bg-red-500 h-full flex items-center justify-center text-xs text-white font-medium"
                                        style={{ width: `${selectedAnalysis.sentiment_negative_percentage}%` }}
                                    >
                                        {selectedAnalysis.sentiment_negative_percentage > 5 ? `Negative ${selectedAnalysis.sentiment_negative_percentage}%` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Main Narratives */}
                    <div className="mb-6">
                        <div className="flex justify-between items-center mb-4">
                            <h4 className="text-xl font-semibold text-white">Main Narratives</h4>
                            <div className="text-sm">
                                <span className="font-medium">Confidence: </span>
                                <span>{(selectedAnalysis.main_narrative_confidence * 100).toFixed(0)}%</span>
                            </div>
                        </div>

                        {renderNarrativeSection(
                            selectedAnalysis.main_narrative_theme_1,
                            selectedAnalysis.main_narrative_coverage_1,
                            selectedAnalysis.main_narrative_examples_1,
                            1
                        )}
                        {renderNarrativeSection(
                            selectedAnalysis.main_narrative_theme_2,
                            selectedAnalysis.main_narrative_coverage_2,
                            selectedAnalysis.main_narrative_examples_2,
                            2
                        )}
                        {renderNarrativeSection(
                            selectedAnalysis.main_narrative_theme_3,
                            selectedAnalysis.main_narrative_coverage_3,
                            selectedAnalysis.main_narrative_examples_3,
                            3
                        )}
                        {renderNarrativeSection(
                            selectedAnalysis.main_narrative_theme_4,
                            selectedAnalysis.main_narrative_coverage_4,
                            selectedAnalysis.main_narrative_examples_4,
                            4
                        )}
                        {renderNarrativeSection(
                            selectedAnalysis.main_narrative_theme_5,
                            selectedAnalysis.main_narrative_coverage_5,
                            selectedAnalysis.main_narrative_examples_5,
                            5
                        )}
                    </div>

                    {/* Promoted Values */}
                    {(selectedAnalysis.values_promoted_value_1 ||
                        selectedAnalysis.values_promoted_value_2 ||
                        selectedAnalysis.values_promoted_value_3) && (
                            <div className="mb-6">
                                <div className="flex justify-between items-center mb-4">
                                    <h4 className="text-xl font-semibold text-white">Promoted Values</h4>
                                    <div className="text-sm">
                                        <span className="font-medium">Confidence: </span>
                                        <span>{(selectedAnalysis.values_promoted_confidence * 100).toFixed(0)}%</span>
                                    </div>
                                </div>

                                {selectedAnalysis.values_promoted_value_1 && (
                                    <div className="mb-4 p-4 bg-gray-700 rounded-lg shadow">
                                        <h5 className="font-bold mb-2">{selectedAnalysis.values_promoted_value_1}</h5>
                                        <p className="text-sm text-gray-300">
                                            {selectedAnalysis.values_promoted_examples_1}
                                        </p>
                                    </div>
                                )}

                                {selectedAnalysis.values_promoted_value_2 && (
                                    <div className="mb-4 p-4 bg-gray-700 rounded-lg shadow">
                                        <h5 className="font-bold mb-2">{selectedAnalysis.values_promoted_value_2}</h5>
                                        <p className="text-sm text-gray-300">
                                            {selectedAnalysis.values_promoted_examples_2}
                                        </p>
                                    </div>
                                )}

                                {selectedAnalysis.values_promoted_value_3 && (
                                    <div className="mb-4 p-4 bg-gray-700 rounded-lg shadow">
                                        <h5 className="font-bold mb-2">{selectedAnalysis.values_promoted_value_3}</h5>
                                        <p className="text-sm text-gray-300">
                                            {selectedAnalysis.values_promoted_examples_3}
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}

                    {/* Analysis Metadata */}
                    <div className="text-xs text-gray-400 mt-8">
                        <p>Analysis ID: {selectedAnalysis.id}</p>
                        <p>Created: {selectedAnalysis.created_at}</p>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AnalysisView;