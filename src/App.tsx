import React, { useState } from 'react';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('sync');

  const renderContent = () => {
    switch (activeTab) {
      case 'sync':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>1-Click <span className="text-gradient">Profile Sync</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '3rem' }}>
              Import your LinkedIn or upload your CV to automatically build your Master Profile. No terminal needed.
            </p>
            <div className="dashboard-grid">
              <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center', border: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.2)' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🔗</div>
                <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Paste LinkedIn URL</h2>
                <input type="text" placeholder="https://linkedin.com/in/username" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1.5rem', outline: 'none' }} />
                <button className="btn btn-primary" style={{ width: '100%' }}>Auto-Sync Profile</button>
              </div>
              <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center', border: '2px dashed var(--border-subtle)', background: 'rgba(0,0,0,0.2)', cursor: 'pointer' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>📄</div>
                <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Upload Existing CV</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>Don't have LinkedIn? Drag and drop your current PDF resume here.</p>
                <button className="btn btn-secondary" style={{ width: '100%' }}>Browse Files</button>
              </div>
            </div>
          </div>
        );
      
      case 'feed':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Live <span className="text-gradient">Job Feed</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)' }}>
              Swipe through scraped jobs matched against your Master Profile.
            </p>
            <div className="tinder-feed">
              <div className="glass-panel job-card">
                <h2 style={{ marginBottom: '0.5rem' }}>Senior React Developer</h2>
                <h4 style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Stripe • Remote</h4>
                <div style={{ display: 'inline-block', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', padding: '0.5rem 1rem', borderRadius: '20px', fontWeight: 'bold', marginBottom: '2rem' }}>
                  94% Match
                </div>
                <p style={{ color: 'var(--text-muted)', textAlign: 'left', marginBottom: '2rem' }}>
                  Looking for a senior engineer with strong React, TypeScript, and Vite experience.
                </p>
                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                  <button className="btn btn-secondary" style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>Pass ❌</button>
                  <button className="btn btn-primary" style={{ background: 'var(--success)', boxShadow: '0 4px 14px 0 rgba(16, 185, 129, 0.4)' }}>Apply ✅</button>
                </div>
              </div>
            </div>
          </div>
        );

      case 'apply':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>1-Click <span className="text-gradient">PDF Generator</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              No LaTeX required. Generate ATS-perfect resumes in the browser instantly.
            </p>
            <div className="dashboard-grid">
              <div className="card glass-panel animate-slide-up" style={{ animationDelay: '0.1s' }}>
                <div className="card-header"><div className="card-icon">📄</div><h3 className="card-title">Tailored Resume</h3></div>
                <p className="card-desc">Automatically rewrites your bullets to match the job description keywords without lying or hallucinating.</p>
                <button className="btn btn-primary" style={{ width: '100%' }}>Download PDF</button>
              </div>
              <div className="card glass-panel animate-slide-up" style={{ animationDelay: '0.2s' }}>
                <div className="card-header"><div className="card-icon">✉️</div><h3 className="card-title">Cover Letter AI</h3></div>
                <p className="card-desc">Generates a genuine, human-sounding cover letter to help you stand out to hiring managers.</p>
                <button className="btn btn-secondary" style={{ width: '100%' }}>Generate Draft</button>
              </div>
            </div>
          </div>
        );

      case 'interview':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Interview <span className="text-gradient">Simulator</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              We know interviewing is incredibly stressful. Practice here first to build your confidence in a safe space.
            </p>
            
            <div className="dashboard-grid" style={{ marginTop: 0 }}>
              <div className="glass-panel" style={{ padding: '1rem', height: '400px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
                <div style={{ background: '#000', flex: 1, borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                  <div style={{ color: 'var(--text-muted)' }}>[ Video Feed Placeholder ]</div>
                </div>
                <div style={{ padding: '1rem 0 0 0', display: 'flex', gap: '1rem' }}>
                  <button className="btn btn-primary" style={{ flex: 1 }}>🎙️ Start Speaking</button>
                  <button className="btn btn-secondary">⏸️ Pause</button>
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <h3>Confidence Coach</h3>
                <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>💡 "You are speaking a bit fast. Take a deep breath. It is totally okay to pause and think about your answer!"</p>
                </div>
                <div style={{ marginTop: 'auto' }}>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Current Question:</p>
                  <p style={{ fontStyle: 'italic' }}>"Tell me about a time you had to pivot quickly on a project."</p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'kanban':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Application <span className="text-gradient">Tracker</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Track your progress. Remember: The 2026 market is tough. A 3% callback rate is normal right now. Keep going, you only need one "Yes".
            </p>
            
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem', padding: '1.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Total Applications</div>
                <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>142</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Interviews</div>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>4</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Market Reality Check</div>
                <div style={{ fontSize: '1rem', marginTop: '0.5rem', color: 'var(--success)' }}>You are performing slightly above average for this quarter! Keep pushing.</div>
              </div>
            </div>

            <div className="kanban-board" style={{ marginTop: 0 }}>
              <div className="kanban-col">
                <h3 style={{ marginBottom: '1rem' }}>Applied (1)</h3>
                <div className="kanban-card">
                  <h4 style={{ marginBottom: '0.2rem' }}>Frontend Engineer</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Vercel</p>
                </div>
              </div>
              <div className="kanban-col">
                <h3 style={{ marginBottom: '1rem' }}>Interviewing (1)</h3>
                <div className="kanban-card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
                  <h4 style={{ marginBottom: '0.2rem' }}>Senior React Dev</h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Stripe</p>
                </div>
              </div>
              <div className="kanban-col">
                <h3 style={{ marginBottom: '1rem' }}>Offers (0)</h3>
              </div>
            </div>
          </div>
        );

      case 'salary':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Fair Pay <span className="text-gradient">Advocate</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Companies are leveraging the bad economy to lowball candidates. We will help you review your offer and provide respectful, professional scripts to ask for what you deserve.
            </p>
            <div className="dashboard-grid">
              <div className="card glass-panel" style={{ gridColumn: 'span 2' }}>
                <h3 style={{ marginBottom: '1rem' }}>Paste Your Offer Details</h3>
                <textarea placeholder="e.g. They offered $110k base, no equity, but the market average is $130k..." style={{ width: '100%', height: '150px', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1.5rem', outline: 'none', fontFamily: 'Inter' }} />
                <button className="btn btn-primary">Generate Respectful Counter-Offer Draft</button>
              </div>
            </div>
          </div>
        );
        
      case 'upskill':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Gap <span className="text-gradient">Heatmap</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Don't get overwhelmed by long requirements lists. Here are the 2 highest-ROI skills you should learn this weekend to drastically increase your chances.
            </p>
            <div className="dashboard-grid">
              <div className="card glass-panel" style={{ borderLeft: '4px solid var(--danger)' }}>
                <h3 style={{ marginBottom: '0.5rem' }}>GraphQL</h3>
                <p style={{ color: 'var(--text-muted)' }}>Missing in 80% of matched jobs.</p>
                <button className="btn btn-secondary" style={{ marginTop: '1rem', fontSize: '0.8rem', padding: '0.5rem 1rem' }}>Watch Free Crash Course ↗</button>
              </div>
              <div className="card glass-panel" style={{ borderLeft: '4px solid var(--warning)' }}>
                <h3 style={{ marginBottom: '0.5rem' }}>Docker</h3>
                <p style={{ color: 'var(--text-muted)' }}>Missing in 45% of matched jobs.</p>
                <button className="btn btn-secondary" style={{ marginTop: '1rem', fontSize: '0.8rem', padding: '0.5rem 1rem' }}>Watch Free Crash Course ↗</button>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="text-gradient">🚀</span> GetHired
        </div>
        <div style={{ padding: '1.5rem 0', flex: 1, overflowY: 'auto' }}>
          <div className={`nav-item ${activeTab === 'sync' ? 'active' : ''}`} onClick={() => setActiveTab('sync')}>🔗 1-Click Sync</div>
          <div className={`nav-item ${activeTab === 'feed' ? 'active' : ''}`} onClick={() => setActiveTab('feed')}>🔍 Job Feed</div>
          <div className={`nav-item ${activeTab === 'apply' ? 'active' : ''}`} onClick={() => setActiveTab('apply')}>📄 Apply Package</div>
          <div className={`nav-item ${activeTab === 'kanban' ? 'active' : ''}`} onClick={() => setActiveTab('kanban')}>📊 Tracker Board</div>
          <div className={`nav-item ${activeTab === 'interview' ? 'active' : ''}`} onClick={() => setActiveTab('interview')}>🤖 Interview Prep</div>
          <div className={`nav-item ${activeTab === 'salary' ? 'active' : ''}`} onClick={() => setActiveTab('salary')}>💰 Fair Pay Advocate</div>
          <div className={`nav-item ${activeTab === 'upskill' ? 'active' : ''}`} onClick={() => setActiveTab('upskill')}>🔥 Gap Heatmap</div>
        </div>
        <div style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))' }}></div>
            <div>
              <div style={{ fontWeight: 'bold' }}>Tahiram32</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Master Profile</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
          {renderContent()}
        </div>
      </main>
    </div>
  );
}

export default App;
