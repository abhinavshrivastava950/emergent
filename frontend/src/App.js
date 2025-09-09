import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Emotion color mapping
const emotionColors = {
  happy: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  sad: 'bg-blue-100 text-blue-800 border-blue-300',
  anxious: 'bg-orange-100 text-orange-800 border-orange-300',
  excited: 'bg-pink-100 text-pink-800 border-pink-300',
  calm: 'bg-green-100 text-green-800 border-green-300',
  angry: 'bg-red-100 text-red-800 border-red-300',
  grateful: 'bg-purple-100 text-purple-800 border-purple-300',
  stressed: 'bg-gray-100 text-gray-800 border-gray-300',
  content: 'bg-teal-100 text-teal-800 border-teal-300',
  melancholy: 'bg-indigo-100 text-indigo-800 border-indigo-300',
  neutral: 'bg-gray-100 text-gray-600 border-gray-300'
};

// Mood score colors for visualization
const getMoodColor = (score) => {
  if (score >= 8) return '#22c55e'; // green
  if (score >= 6) return '#84cc16'; // lime
  if (score >= 4) return '#eab308'; // yellow
  if (score >= 2) return '#f97316'; // orange
  return '#ef4444'; // red
};

const JournalApp = () => {
  const [entries, setEntries] = useState([]);
  const [newEntry, setNewEntry] = useState({ title: '', content: '', tags: [] });
  const [currentTag, setCurrentTag] = useState('');
  const [loading, setLoading] = useState(false);
  const [moodTrends, setMoodTrends] = useState(null);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [activeTab, setActiveTab] = useState('write');

  // Fetch entries
  const fetchEntries = async () => {
    try {
      const response = await axios.get(`${API}/entries`);
      setEntries(response.data);
    } catch (error) {
      console.error('Error fetching entries:', error);
    }
  };

  // Fetch mood trends
  const fetchMoodTrends = async () => {
    try {
      const response = await axios.get(`${API}/mood-trends/weekly`);
      setMoodTrends(response.data);
    } catch (error) {
      console.error('Error fetching mood trends:', error);
    }
  };

  useEffect(() => {
    fetchEntries();
    fetchMoodTrends();
  }, []);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newEntry.title.trim() || !newEntry.content.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API}/entries`, newEntry);
      setEntries([response.data, ...entries]);
      setNewEntry({ title: '', content: '', tags: [] });
      setCurrentTag('');
      fetchMoodTrends(); // Refresh trends
    } catch (error) {
      console.error('Error creating entry:', error);
    }
    setLoading(false);
  };

  // Add tag
  const addTag = () => {
    if (currentTag.trim() && !newEntry.tags.includes(currentTag.trim())) {
      setNewEntry({
        ...newEntry,
        tags: [...newEntry.tags, currentTag.trim()]
      });
      setCurrentTag('');
    }
  };

  // Remove tag
  const removeTag = (tagToRemove) => {
    setNewEntry({
      ...newEntry,
      tags: newEntry.tags.filter(tag => tag !== tagToRemove)
    });
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  // Line Chart Component (Simple SVG)
  const LineChart = ({ data }) => {
    if (!data || data.length === 0) return <div className="text-gray-500">No data available</div>;

    const width = 400;
    const height = 200;
    const margin = 40;
    const chartWidth = width - 2 * margin;
    const chartHeight = height - 2 * margin;

    const maxScore = Math.max(...data.map(d => d.mood_score));
    const minScore = Math.min(...data.map(d => d.mood_score));
    const scoreRange = maxScore - minScore || 1;

    const points = data.map((d, i) => {
      const x = margin + (i * chartWidth) / (data.length - 1 || 1);
      const y = margin + chartHeight - ((d.mood_score - minScore) / scoreRange) * chartHeight;
      return `${x},${y}`;
    }).join(' ');

    return (
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <h4 className="font-semibold text-gray-800 mb-3">Mood Trend (Line Chart)</h4>
        <svg width={width} height={height} className="border rounded">
          {/* Grid lines */}
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(score => {
            const y = margin + chartHeight - ((score - minScore) / scoreRange) * chartHeight;
            return (
              <g key={score}>
                <line x1={margin} y1={y} x2={width - margin} y2={y} stroke="#f0f0f0" strokeWidth="1"/>
                <text x={margin - 5} y={y + 4} fontSize="10" fill="#666" textAnchor="end">{score}</text>
              </g>
            );
          })}
          
          {/* Line */}
          <polyline
            points={points}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Points */}
          {data.map((d, i) => {
            const x = margin + (i * chartWidth) / (data.length - 1 || 1);
            const y = margin + chartHeight - ((d.mood_score - minScore) / scoreRange) * chartHeight;
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r="4"
                fill={getMoodColor(d.mood_score)}
                stroke="white"
                strokeWidth="2"
              />
            );
          })}
          
          {/* Date labels */}
          {data.map((d, i) => {
            const x = margin + (i * chartWidth) / (data.length - 1 || 1);
            return (
              <text
                key={i}
                x={x}
                y={height - 10}
                fontSize="10"
                fill="#666"
                textAnchor="middle"
              >
                {new Date(d.date).getDate()}
              </text>
            );
          })}
        </svg>
      </div>
    );
  };

  // Bar Chart Component (Simple SVG)
  const BarChart = ({ data }) => {
    if (!data || data.length === 0) return <div className="text-gray-500">No data available</div>;

    const width = 400;
    const height = 200;
    const margin = 40;
    const chartWidth = width - 2 * margin;
    const chartHeight = height - 2 * margin;
    const barWidth = chartWidth / data.length * 0.8;

    return (
      <div className="bg-white p-4 rounded-lg shadow-sm border">
        <h4 className="font-semibold text-gray-800 mb-3">Mood Trend (Bar Chart)</h4>
        <svg width={width} height={height} className="border rounded">
          {/* Grid lines */}
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(score => {
            const y = margin + chartHeight - (score / 10) * chartHeight;
            return (
              <g key={score}>
                <line x1={margin} y1={y} x2={width - margin} y2={y} stroke="#f0f0f0" strokeWidth="1"/>
                <text x={margin - 5} y={y + 4} fontSize="10" fill="#666" textAnchor="end">{score}</text>
              </g>
            );
          })}
          
          {/* Bars */}
          {data.map((d, i) => {
            const x = margin + (i * chartWidth) / data.length + (chartWidth / data.length - barWidth) / 2;
            const barHeight = (d.mood_score / 10) * chartHeight;
            const y = margin + chartHeight - barHeight;
            
            return (
              <g key={i}>
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barHeight}
                  fill={getMoodColor(d.mood_score)}
                  rx="3"
                />
                <text
                  x={x + barWidth / 2}
                  y={y - 5}
                  fontSize="10"
                  fill="#666"
                  textAnchor="middle"
                >
                  {d.mood_score}
                </text>
                <text
                  x={x + barWidth / 2}
                  y={height - 10}
                  fontSize="10"
                  fill="#666"
                  textAnchor="middle"
                >
                  {new Date(d.date).getDate()}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">✨ My Journal</h1>
          <p className="text-gray-600">Track your thoughts, emotions, and mood journey</p>
        </header>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg shadow-sm border p-1">
            <button
              onClick={() => setActiveTab('write')}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'write'
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Write Entry
            </button>
            <button
              onClick={() => setActiveTab('entries')}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'entries'
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              My Entries
            </button>
            <button
              onClick={() => setActiveTab('trends')}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                activeTab === 'trends'
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Mood Trends
            </button>
          </div>
        </div>

        {/* Write Entry Tab */}
        {activeTab === 'write' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-xl shadow-lg border p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">Write New Entry</h2>
              
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Entry Title
                  </label>
                  <input
                    type="text"
                    value={newEntry.title}
                    onChange={(e) => setNewEntry({ ...newEntry, title: e.target.value })}
                    placeholder="Give your entry a title..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Your Thoughts
                  </label>
                  <textarea
                    value={newEntry.content}
                    onChange={(e) => setNewEntry({ ...newEntry, content: e.target.value })}
                    placeholder="Write about your day, thoughts, feelings..."
                    rows={8}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Tags
                  </label>
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={currentTag}
                      onChange={(e) => setCurrentTag(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                      placeholder="Add a tag..."
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Add
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {newEntry.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800 border border-blue-200"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(tag)}
                          className="ml-2 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading || !newEntry.title.trim() || !newEntry.content.trim()}
                  className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02]"
                >
                  {loading ? '✨ Analyzing your mood...' : '📝 Save Entry'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Entries Tab */}
        {activeTab === 'entries' && (
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">My Journal Entries</h2>
            
            {entries.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📖</div>
                <p className="text-gray-600 text-lg">No entries yet. Start writing to track your mood journey!</p>
              </div>
            ) : (
              <div className="space-y-6">
                {entries.map((entry) => (
                  <div
                    key={entry.id}
                    className="bg-white rounded-xl shadow-lg border hover:shadow-xl transition-shadow cursor-pointer"
                    onClick={() => setSelectedEntry(selectedEntry?.id === entry.id ? null : entry)}
                  >
                    <div className="p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <h3 className="text-xl font-bold text-gray-800 mb-2">{entry.title}</h3>
                          <p className="text-gray-600 text-sm">{formatDate(entry.date)}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          {entry.mood_score && (
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                                style={{ backgroundColor: getMoodColor(entry.mood_score) }}
                              >
                                {entry.mood_score}
                              </div>
                              {entry.mood_emotion && (
                                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${emotionColors[entry.mood_emotion] || emotionColors.neutral}`}>
                                  {entry.mood_emotion}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      {selectedEntry?.id === entry.id && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <div className="prose prose-gray max-w-none mb-4">
                            <p className="text-gray-700 leading-relaxed">{entry.content}</p>
                          </div>
                          
                          {entry.ai_summary && (
                            <div className="bg-blue-50 rounded-lg p-4 mb-4">
                              <h4 className="font-semibold text-blue-800 mb-2">🤖 AI Summary</h4>
                              <p className="text-blue-700">{entry.ai_summary}</p>
                            </div>
                          )}

                          {entry.tags && entry.tags.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                              {entry.tags.map((tag, index) => (
                                <span
                                  key={index}
                                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm border"
                                >
                                  #{tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Trends Tab */}
        {activeTab === 'trends' && (
          <div className="max-w-6xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Weekly Mood Trends</h2>
            
            {moodTrends ? (
              <div className="space-y-8">
                {/* Stats Cards */}
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="bg-white rounded-xl shadow-lg p-6 text-center">
                    <div className="text-3xl font-bold text-blue-600 mb-2">
                      {moodTrends.average_mood}/10
                    </div>
                    <div className="text-gray-600">Average Mood</div>
                  </div>
                  <div className="bg-white rounded-xl shadow-lg p-6 text-center">
                    <div className={`text-2xl font-bold mb-2 px-4 py-2 rounded-full ${emotionColors[moodTrends.most_common_emotion] || emotionColors.neutral}`}>
                      {moodTrends.most_common_emotion}
                    </div>
                    <div className="text-gray-600">Most Common Emotion</div>
                  </div>
                  <div className="bg-white rounded-xl shadow-lg p-6 text-center">
                    <div className="text-3xl font-bold text-green-600 mb-2">
                      {moodTrends.total_entries}
                    </div>
                    <div className="text-gray-600">Entries This Week</div>
                  </div>
                </div>

                {/* Charts */}
                {moodTrends.weekly_trends.length > 0 ? (
                  <div className="grid lg:grid-cols-2 gap-8">
                    <LineChart data={moodTrends.weekly_trends} />
                    <BarChart data={moodTrends.weekly_trends} />
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">📊</div>
                    <p className="text-gray-600 text-lg">No mood data available for this week. Write some entries to see your trends!</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="animate-spin text-4xl mb-4">⭕</div>
                <p className="text-gray-600">Loading mood trends...</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default JournalApp;