// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import PoliticalSpectrum from './components/PoliticalSpectrum.jsx';
import MediaSourceCard from './components/MediaSourceCard.jsx';
import AnalysisView from './components/AnalysisView.jsx';
import ArticleExplorer from './components/ArticleExplorer.jsx';
import { FaChartBar, FaNewspaper, FaGlobe } from 'react-icons/fa';
import './overflow-fix.css';

function App() {
  const [mediaSources, setMediaSources] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [activeTab, setActiveTab] = useState('spectrum');
  const [isLoading, setIsLoading] = useState(false);

  // Use environment variables for API URL (ensure VITE_API_URL_DEV is set, e.g., in .env file)
  const API_URL = import.meta.env.VITE_API_URL_DEV || 'http://localhost:8000';

  useEffect(() => {
    // Fetch all media sources on component mount
    axios.get(`${API_URL}/media_sources`)
      .then(response => setMediaSources(response.data))
      .catch(error => console.error('Error fetching media sources:', error));
  }, [API_URL]);

  // Fetch analyses when a source is selected
  useEffect(() => {
    if (selectedSource) {
      setIsLoading(true);
      axios.get(`${API_URL}/analyses`, { params: { source: selectedSource.source } })
        .then(response => {
          setAnalyses(response.data);
        })
        .catch(error => {
          console.error('Error fetching analyses for source:', error);
          setAnalyses([]);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [selectedSource, API_URL]);

  return (
    <div className="dark min-h-screen bg-gray-900 text-white transition-colors duration-300 flex flex-col relative">
      {/* Beta ribbon */}
      <div className="absolute top-0 right-0 z-50">
        <div className="bg-yellow-500 text-yellow-900 font-bold py-1 px-4 shadow-md transform rotate-45 translate-x-8 -translate-y-2">
          BETA
        </div>
      </div>

      {/* Hero Header - Set dark gradient directly */}
      <header className="bg-gradient-to-r from-blue-800 to-indigo-900 shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            {/* Logo and Title Section */}
            <div className="flex items-center">
              <div className="w-16 h-16 mr-4 flex-shrink-0 bg-white/10 rounded-full p-1">
                <img src="/logo.svg" alt="Concordia Logo" className="w-full h-full" />
              </div>
              <div>
                <div className="flex items-center">
                  <h1 className="text-3xl font-bold text-white">Concordia</h1>
                  <span className="ml-2 px-2 py-1 text-xs font-bold bg-yellow-500 text-yellow-900 rounded-md">BETA</span>
                </div>
                <p className="text-sm text-white/80 italic">Harmony in the Noise</p>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex mt-8 border-b border-white/20">
            <button
              className={`px-4 py-2 text-white font-medium transition-colors ${activeTab === 'spectrum' ? 'border-b-2 border-white' : 'opacity-70 hover:opacity-100'}`}
              onClick={() => setActiveTab('spectrum')}
            >
              <FaGlobe className="inline mr-2" /> Media Spectrum
            </button>
            <button
              className={`px-4 py-2 text-white font-medium transition-colors ${activeTab === 'articles' ? 'border-b-2 border-white' : 'opacity-70 hover:opacity-100'}`}
              onClick={() => setActiveTab('articles')}
            >
              <FaNewspaper className="inline mr-2" /> Article Explorer
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 flex-grow">
        {activeTab === 'spectrum' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div className="mb-8 bg-gray-800 rounded-lg shadow-lg overflow-hidden">
              <div className="p-4 bg-gray-700 border-b border-gray-600">
                <h2 className="text-xl font-semibold">Political Bias Spectrum</h2>
                <p className="text-sm text-gray-400">
                  Click on a media source to view detailed analysis
                </p>
              </div>
              <div className="p-4">
                <PoliticalSpectrum
                  mediaSources={mediaSources}
                  onSelectSource={(source) => {
                    setSelectedSource(source);
                    window.scrollTo({ top: document.getElementById('source-details')?.offsetTop - 100, behavior: 'smooth' });
                  }}
                />
              </div>
            </div>

            {selectedSource && (
              <motion.div
                id="source-details"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="grid grid-cols-1 gap-6 lg:grid-cols-2"
              >
                <MediaSourceCard mediaSource={selectedSource} />
                {isLoading ? (
                  <div className="flex justify-center p-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                  </div>
                ) : (
                  <AnalysisView analyses={analyses} />
                )}
              </motion.div>
            )}
          </motion.div>
        )}

        {activeTab === 'articles' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <ArticleExplorer />
          </motion.div>
        )}
      </main>

      <footer className="bg-gray-800 border-t border-gray-700 py-6">
        <div className="container mx-auto px-4 text-center text-gray-400 text-sm">
          <p>© {new Date().getFullYear()} Concordia. All rights reserved.</p>
          <p className="mt-2">Harmony in the Noise: Analyzing media bias and narratives across the political spectrum.</p>
          <div className="mt-4 flex justify-center space-x-4">
            <a href="/terms.html" target="_blank" rel="noopener noreferrer" className="hover:text-blue-400 transition-colors">Terms of Service</a>
            <span>•</span>
            <a href="/privacy.html" target="_blank" rel="noopener noreferrer" className="hover:text-blue-400 transition-colors">Privacy Policy</a>
            <span>•</span>
            <a href="mailto:concordia.news@proton.me" className="hover:text-blue-400 transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;