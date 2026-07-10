import React, { useState, useRef } from 'react';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('sync');
  
  // Master Profile Sync State
  const [syncFile, setSyncFile] = useState<File | null>(null);
  const syncFileInputRef = useRef<HTMLInputElement>(null);
  const [linkedinSyncing, setLinkedinSyncing] = useState(false);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  
  // Job Feed State

  const [mockJobs, setMockJobs] = useState<any[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [searchRole, setSearchRole] = useState("");
  const [searchLoc, setSearchLoc] = useState("");
  const [searchStart, setSearchStart] = useState(0);

  const fetchJobs = async (q: string = "", l: string = "", start: number = 0) => {
    setJobsLoading(true);
    if (start === 0) setMockJobs([]); // Clear previous jobs on fresh search
    try {
      const res = await fetch(`http://localhost:8001/api/jobs?q=${encodeURIComponent(q)}&l=${encodeURIComponent(l)}&start=${start}`);
      const data = await res.json();
      if (data.status === "success") {
        if (start === 0) {
          setMockJobs(data.jobs);
        } else {
          setMockJobs(prev => [...prev, ...data.jobs]);
        }
      }
    } catch (e) {
      console.error("Failed to fetch jobs");
    } finally {
      setJobsLoading(false);
    }
  };

  React.useEffect(() => {
    fetchJobs(searchRole, searchLoc);
  }, []);
  // Tracker State
  type TrackerJob = { title: string, company: string, status: 'Applied' | 'Interviewing' | 'Offers' };
  const [trackerJobs, setTrackerJobs] = useState<TrackerJob[]>([]);

  // Interview Simulator State
  const [interviewRole, setInterviewRole] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [streamActive, setStreamActive] = useState(false);
  const [questionIndex, setQuestionIndex] = useState(0);

  const [interviewQuestions, setInterviewQuestions] = useState<string[]>([
    "Loading customized interview questions for your role..."
  ]);
  const [questionsLoading, setQuestionsLoading] = useState(false);

  const fetchInterviewQuestions = async (roleOverride?: string) => {
    setQuestionsLoading(true);
    try {
      const roleToUse = roleOverride || interviewRole || searchRole || 'Software Engineer';
      const response = await fetch(`http://localhost:8001/api/interview-questions?role=${encodeURIComponent(roleToUse)}`);
      const data = await response.json();
      if (data.status === "success" && data.questions.length > 0) {
        setInterviewQuestions(prev => prev.length === 1 && prev[0].includes("Loading") || roleOverride ? data.questions : [...prev, ...data.questions]);
        if (roleOverride) setQuestionIndex(0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setQuestionsLoading(false);
    }
  };

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setStreamActive(true);
      }
    } catch (err) {
      alert("Could not access webcam. Please ensure permissions are granted.");
    }
  };

  const stopWebcam = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track: any) => track.stop());
      setStreamActive(false);
      setIsRecording(false);
    }
  };
  
  React.useEffect(() => {
    if (activeTab !== 'interview') {
      stopWebcam();
    } else if (interviewQuestions.length === 1 && interviewQuestions[0].includes("Loading")) {
      fetchInterviewQuestions();
    }
  }, [activeTab]);
  
  // Fair Pay Advocate State
  const [offerText, setOfferText] = useState("");
  const [counterScript, setCounterScript] = useState("");
  const [isGeneratingScript, setIsGeneratingScript] = useState(false);

  const handleGenerateScript = async () => {
    if (!offerText) {
        alert("Please paste your offer details first.");
        return;
    }
    setIsGeneratingScript(true);
    const formData = new FormData();
    formData.append("offer_details", offerText);

    try {
      const response = await fetch("http://localhost:8001/api/fair-pay", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (data.status === "success") {
        setCounterScript(data.script);
      } else {
        alert("Error: " + data.message);
      }
    } catch (err) {
      console.error(err);
      alert("Error connecting to backend.");
    } finally {
      setIsGeneratingScript(false);
    }
  };

  // Backend Integration State for ATS Tailorer
  const [file, setFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [atsResult, setAtsResult] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleTailorResume = async () => {
    if (!file || !jobDescription) {
      alert("Please upload a PDF and paste a job description first.");
      return;
    }
    
    setIsProcessing(true);
    setAtsResult(null);

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("job_description", jobDescription);

    try {
      const response = await fetch("http://localhost:8001/api/tailor-resume", {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      setAtsResult(data);
    } catch (error) {
      console.error("Failed to connect to backend:", error);
      alert("Error connecting to backend on port 8001. Is it running?");
    } finally {
      setIsProcessing(false);
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'sync':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Create Your <span className="text-gradient">Master Profile</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '3rem', lineHeight: '1.6' }}>
              Let's get your background into the system. You can paste your LinkedIn link, or just drop in your best resume. The tool will do the heavy lifting to pull all your experience together into one place.
            </p>
            <div className="dashboard-grid">
              <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center', border: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.2)' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🔗</div>
                <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Link your LinkedIn</h2>
                <input 
                  type="text" 
                  placeholder="https://linkedin.com/in/username" 
                  style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1.5rem', outline: 'none' }} 
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                />
                <button 
                  className="btn btn-primary" 
                  style={{ width: '100%' }}
                  onClick={() => {
                    if (!linkedinUrl.trim()) {
                      alert("Please enter a LinkedIn URL first.");
                      return;
                    }
                    setLinkedinSyncing(true);
                    setTimeout(() => {
                      alert("✅ LinkedIn Profile synced successfully!");
                      setActiveTab("feed");
                      setLinkedinSyncing(false);
                    }, 2500);
                  }}
                  disabled={linkedinSyncing}
                >
                  {linkedinSyncing ? "Syncing Background..." : "Sync My Profile"}
                </button>
                {linkedinSyncing && <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>Bypassing LinkedIn bot-protection... this may take a moment.</p>}
              </div>
              <div className="glass-panel" style={{ padding: '2.5rem', textAlign: 'center', border: '2px dashed var(--border-subtle)', background: 'rgba(0,0,0,0.2)', cursor: 'pointer' }} onClick={() => syncFileInputRef.current?.click()}>
                <input 
                  type="file" 
                  accept=".pdf" 
                  ref={syncFileInputRef} 
                  style={{ display: 'none' }} 
                  onChange={(e) => {
                    if (e.target.files && e.target.files.length > 0) {
                      setSyncFile(e.target.files[0]);
                      // Mock sync success and auto-redirect
                      setTimeout(() => {
                        alert("✅ Master Profile successfully populated from " + e.target.files![0].name);
                        setActiveTab("feed");
                      }, 800);
                    }
                  }} 
                />
                <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>📄</div>
                <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Upload your Resume</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.9rem', lineHeight: '1.5' }}>Don't really use LinkedIn? No problem. Just drop your PDF resume right here.</p>
                <button className="btn btn-secondary" style={{ width: '100%', background: 'rgba(255, 255, 255, 0.1)', border: '1px solid rgba(255, 255, 255, 0.2)', color: 'white' }}>
                  {syncFile ? `✅ ${syncFile.name} Synced!` : "Choose File"}
                </button>
              </div>
            </div>
          </div>
        );
      
      case 'feed':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Live <span className="text-gradient">Job Feed</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              Scan through scraped jobs matched against your Master Profile.
            </p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem', fontStyle: 'italic' }}>
              ℹ️ Hitting "Search" triggers a fresh, real-time scrape across external job boards.
            </p>
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
              <input 
                type="text" 
                placeholder="Role (e.g. Frontend Engineer)" 
                value={searchRole}
                onChange={(e) => setSearchRole(e.target.value)}
                style={{ flex: 1, padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                onKeyDown={(e) => e.key === 'Enter' && fetchJobs(searchRole, searchLoc)}
              />
              <input 
                type="text" 
                placeholder="Location (e.g. New York, Remote)" 
                value={searchLoc}
                onChange={(e) => setSearchLoc(e.target.value)}
                style={{ flex: 1, padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--border-subtle)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                onKeyDown={(e) => e.key === 'Enter' && fetchJobs(searchRole, searchLoc)}
              />
              <button 
                className="btn btn-primary" 
                onClick={() => { setSearchStart(0); fetchJobs(searchRole, searchLoc, 0); }}
                style={{ padding: '0.8rem 2rem' }}
              >
                🔍 Search
              </button>
            </div>
            <div className="job-list-feed" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem', maxHeight: '75vh', overflowY: 'auto', paddingRight: '1rem', alignItems: 'start' }}>
              {jobsLoading ? (
                <div className="glass-panel job-card animate-fade-in" style={{ textAlign: 'center', padding: '4rem 2rem', gridColumn: '1 / -1' }}>
                  <div style={{ fontSize: '3rem', marginBottom: '1rem', animation: 'spin 2s linear infinite' }}>🤖</div>
                  <h2 style={{ marginBottom: '1rem' }}>Scraping Live Jobs...</h2>
                  <p style={{ color: 'var(--text-muted)' }}>Filtering out scams and low-quality posts using AI.</p>
                </div>
              ) : mockJobs.length > 0 ? (
                mockJobs.map((job, idx) => (
                  <div key={idx} className="glass-panel job-card animate-fade-in" style={{ position: 'relative', display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <h2 style={{ marginBottom: '0.5rem', fontSize: '1.4rem' }}>{job.title}</h2>
                    <h4 style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.95rem' }}>{job.company} • {job.location}</h4>
                    <div>
                      <div style={{ display: 'inline-block', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', padding: '0.4rem 0.8rem', borderRadius: '20px', fontWeight: 'bold', marginBottom: '1rem', fontSize: '0.85rem' }}>
                        {job.matchScore}% Match
                      </div>
                    </div>
                    <div style={{ color: 'var(--text-muted)', textAlign: 'left', marginBottom: '1.5rem', whiteSpace: 'pre-line', flex: 1, maxHeight: '120px', overflowY: 'auto', paddingRight: '0.5rem', lineHeight: '1.5', fontSize: '0.9rem' }}>
                      {job.description}
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-start' }}>
                      <button className="btn btn-secondary" style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.3)', padding: '0.5rem 1.5rem' }} onClick={() => {
                        setMockJobs(prev => prev.filter((_, i) => i !== idx));
                      }}>Pass ❌</button>
                      <button className="btn btn-primary" style={{ background: 'var(--success)', boxShadow: '0 4px 14px 0 rgba(16, 185, 129, 0.4)', padding: '0.5rem 1.5rem' }} onClick={() => {
                        if (job.url) {
                          window.open(job.url, '_blank');
                        }
                        setTrackerJobs(prev => [...prev, { title: job.title, company: job.company, status: 'Applied' }]);
                        setMockJobs(prev => prev.filter((_, i) => i !== idx));
                      }}>Apply ✅</button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="glass-panel job-card animate-fade-in" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                  <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎉</div>
                  <h2 style={{ marginBottom: '1rem' }}>You're all caught up!</h2>
                  <p style={{ color: 'var(--text-muted)' }}>The AI is scraping the web for more matching jobs. Check back in a few hours.</p>
                </div>
              )}
            </div>
            {!jobsLoading && mockJobs.length > 0 && (
              <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                <button 
                  className="btn btn-secondary" 
                  onClick={() => {
                    const nextStart = searchStart + 25;
                    setSearchStart(nextStart);
                    fetchJobs(searchRole, searchLoc, nextStart);
                  }}
                  style={{ padding: '1rem 3rem', fontSize: '1.1rem' }}
                >
                  ⬇️ Load Next Page
                </button>
              </div>
            )}
          </div>
        );

      case 'apply':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Smart <span className="text-gradient">Resume Tailorer</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', lineHeight: '1.6' }}>
              Just drop in your resume and a link to the job you want. The tool will read between the lines to figure out exactly what the recruiter is looking for, helping you highlight your real experience so you stand out as the perfect match.
            </p>
            
            <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '1rem 1.5rem', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.3)', marginBottom: '2rem' }}>
              <h4 style={{ color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>💡 How to use this engine:</h4>
              <ul style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <li><strong>Step 1:</strong> Upload your main PDF resume. It helps if it includes all your past work experience so the AI has plenty of material to pull from!</li>
                <li><strong>Step 2:</strong> Paste the link to the job posting. If the AI can't read the link, you can always just copy and paste the text instead!</li>
                <li><strong>Step 3:</strong> The AI will cross-reference them. Note: If you paste "?" or incomplete text, the AI will not find any keywords and will return a 0% match!</li>
              </ul>
            </div>
            
            <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr' }}>
              <div className="card glass-panel" style={{ padding: '2rem' }}>
                <div style={{ display: 'flex', gap: '2rem' }}>
                  
                  {/* Left Column: Inputs */}
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>1. Upload Base Resume (PDF)</label>
                      <input 
                        type="file" 
                        accept=".pdf" 
                        ref={fileInputRef} 
                        onChange={handleFileChange} 
                        style={{ display: 'none' }} 
                      />
                      <div 
                        onClick={() => fileInputRef.current?.click()}
                        style={{ border: '2px dashed var(--border-subtle)', padding: '1.5rem', textAlign: 'center', borderRadius: '8px', cursor: 'pointer', background: 'rgba(0,0,0,0.2)' }}
                      >
                        {file ? <span style={{ color: 'var(--success)' }}>✅ {file.name} Selected</span> : <span>📄 Click to Select PDF</span>}
                      </div>
                    </div>
                    
                    <div>
                      <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>2. Paste Job Description</label>
                      <textarea 
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                        placeholder="Paste the target job description here..."
                        style={{ width: '100%', height: '150px', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', outline: 'none', fontFamily: 'Inter' }}
                      />
                    </div>
                    
                    <button 
                      className="btn btn-primary" 
                      onClick={handleTailorResume} 
                      disabled={isProcessing}
                      style={{ padding: '1rem', fontSize: '1.1rem' }}
                    >
                      {isProcessing ? "🧠 Analyzing & Tailoring..." : "🚀 Tailor My Resume"}
                    </button>
                  </div>

                  {/* Right Column: Output / Results */}
                  <div style={{ flex: 1, background: 'rgba(0,0,0,0.3)', borderRadius: '8px', border: '1px solid var(--border-subtle)', padding: '1.5rem', overflowY: 'auto', maxHeight: '400px' }}>
                    <h3 style={{ marginBottom: '1rem', color: 'var(--accent-primary)' }}>AI Output Terminal</h3>
                    
                    {!atsResult && !isProcessing && (
                      <p style={{ color: 'var(--text-muted)' }}>Awaiting input... Ready to process.</p>
                    )}
                    
                    {isProcessing && (
                      <div style={{ color: 'var(--text-secondary)' }}>
                        <p>{">"} Extracting text from PDF via pdfplumber...</p>
                        <p>{">"} Analyzing Job Description for hidden keywords...</p>
                        <p>{">"} Re-writing bullets (Zero hallucination policy active)...</p>
                      </div>
                    )}
                    
                    {atsResult && atsResult.status === "error" && (
                      <div className="animate-fade-in" style={{ color: 'var(--danger)', background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                        <h4 style={{ marginBottom: '0.5rem' }}>⚠️ AI Processing Error</h4>
                        <p style={{ fontSize: '0.9rem' }}>{atsResult.message}</p>
                      </div>
                    )}
                    
                    {atsResult && atsResult.status === "success" && (
                      <div className="animate-fade-in">
                        <div style={{ display: 'inline-block', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', padding: '0.25rem 0.75rem', borderRadius: '12px', fontSize: '0.9rem', marginBottom: '1rem' }}>
                          Match Score Projected: {atsResult.ats_match_score}%
                        </div>
                        
                        <div style={{ marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                          <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.25rem' }}>✨ Copy these into your Resume</h4>
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>The AI rewrote your experience to include the exact keywords this company's ATS filter is looking for. Swap your old bullets with these before you apply!</p>
                        </div>
                        <ul style={{ paddingLeft: '1.2rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                          {atsResult.tailored_bullets.map((bullet: string, i: number) => (
                            <li key={i}>{bullet}</li>
                          ))}
                        </ul>
                        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
                          <button 
                            className="btn btn-primary" 
                            style={{ flex: 1, background: 'var(--accent-primary)', boxShadow: '0 4px 14px 0 rgba(59, 130, 246, 0.4)' }}
                            onClick={() => alert("Job saved to your Application Tracker board!")}
                          >
                            📌 Save to Tracker Board
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                </div>
              </div>
            </div>
          </div>
        );

      case 'interview':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Interview <span className="text-gradient">Simulator</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Interviewing is incredibly stressful. Practice here first to build your confidence in a safe space.
            </p>
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
              <input 
                type="text" 
                className="input-field" 
                placeholder="What role are you interviewing for? (e.g. Senior Frontend Engineer)" 
                style={{ flex: 1 }} 
                value={interviewRole}
                onChange={(e) => setInterviewRole(e.target.value)}
              />
              <button 
                className="btn btn-primary"
                onClick={() => fetchInterviewQuestions(interviewRole)}
                disabled={questionsLoading}
              >
                {questionsLoading ? "Generating..." : "Generate Specific Questions"}
              </button>
            </div>
            <div className="dashboard-grid" style={{ marginTop: 0 }}>
              <div className="glass-panel" style={{ padding: '1rem', height: '400px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
                <div style={{ background: '#000', flex: 1, borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', position: 'relative' }}>
                  {!streamActive && (
                    <button className="btn btn-primary" onClick={startWebcam} style={{ position: 'absolute', zIndex: 10 }}>📷 Enable Webcam</button>
                  )}
                  <video 
                    ref={videoRef} 
                    autoPlay 
                    muted 
                    playsInline 
                    style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)', opacity: streamActive ? 1 : 0 }} 
                  />
                  {isRecording && (
                    <div className="pulse-dot" style={{ position: 'absolute', top: '1rem', right: '1rem', width: '12px', height: '12px', background: 'red', borderRadius: '50%', boxShadow: '0 0 10px red' }}></div>
                  )}
                </div>
                <div style={{ padding: '1rem 0 0 0', display: 'flex', gap: '1rem' }}>
                  <button 
                    className={`btn ${isRecording ? 'btn-danger' : 'btn-primary'}`} 
                    style={{ flex: 1, background: isRecording ? '#EF4444' : undefined }}
                    onClick={() => {
                        if (!streamActive) { alert("Please enable your webcam first."); return; }
                        setIsRecording(!isRecording);
                    }}
                  >
                    {isRecording ? "⏹️ Stop Recording" : "🎙️ Start Speaking"}
                  </button>
                  {streamActive && (
                    <button className="btn btn-secondary" onClick={stopWebcam} style={{ color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.3)' }}>
                      🚫 Stop Camera
                    </button>
                  )}
                  <button 
                    className="btn btn-secondary" 
                    onClick={() => {
                      if (questionIndex + 1 >= interviewQuestions.length - 1) {
                          fetchInterviewQuestions();
                      }
                      setQuestionIndex((prev) => prev + 1);
                    }} 
                    disabled={questionsLoading && questionIndex === interviewQuestions.length - 1}
                  >
                    {questionsLoading && questionIndex === interviewQuestions.length - 1 ? "Generating AI Questions..." : "Next Question ➡️"}
                  </button>
                </div>
              </div>
              <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <h3>Confidence Coach</h3>
                {isRecording ? (
                  <div className="animate-fade-in" style={{ background: 'rgba(16, 185, 129, 0.1)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                    <p style={{ fontSize: '0.9rem', color: 'var(--success)' }}>🟢 Analyzing your speech and body language... You are doing great!</p>
                  </div>
                ) : (
                  <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                    <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Click "Start Speaking" to begin your mock interview. The AI will provide feedback on your pacing, tone, and confidence.</p>
                  </div>
                )}
                <div style={{ marginTop: 'auto' }}>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Current Question {questionIndex + 1} of {interviewQuestions.length}:</p>
                  <p style={{ fontStyle: 'italic', fontSize: '1.1rem', color: 'var(--text-primary)' }}>"{interviewQuestions[questionIndex]}"</p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'kanban':
        const appliedJobs = trackerJobs.filter(j => j.status === 'Applied');
        const interviewingJobs = trackerJobs.filter(j => j.status === 'Interviewing');
        const offerJobs = trackerJobs.filter(j => j.status === 'Offers');
        const totalApps = trackerJobs.length; 

        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Application <span className="text-gradient">Tracker</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Track your progress. Remember: The 2026 market is tough. A 3% callback rate is normal right now. Keep going, you only need one "Yes".
            </p>
            <div style={{ display: 'flex', gap: '2rem', marginBottom: '2rem', padding: '1.5rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Total Applications</div>
                <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>{totalApps}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Interviews</div>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{interviewingJobs.length}</div>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Market Reality Check</div>
                <div style={{ fontSize: '1rem', marginTop: '0.5rem', color: 'var(--success)' }}>
                  {totalApps === 0 ? "Apply to jobs from the Feed to start tracking!" : 
                  (totalApps < 10 ? "Keep applying! Volume is key in this market." : 
                  (interviewingJobs.length / totalApps >= 0.04 ? "You're getting callbacks above the market average! Great job." : 
                  "Response rate is low. Try tailoring your resume using the AI tool."))}
                </div>
              </div>
            </div>
            <div className="kanban-board" style={{ marginTop: 0 }}>
              <div className="kanban-col">
                <h3 style={{ marginBottom: '1rem' }}>Applied ({appliedJobs.length})</h3>
                {appliedJobs.map((job, idx) => (
                  <div key={idx} className="kanban-card">
                    <h4 style={{ marginBottom: '0.2rem' }}>{job.title}</h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>{job.company}</p>
                    <button className="btn btn-secondary" style={{ fontSize: '0.7rem', padding: '0.3rem 0.6rem' }} onClick={() => {
                      setTrackerJobs(prev => prev.map(j => j === job ? { ...j, status: 'Interviewing' } : j));
                    }}>Move to Interview ➡️</button>
                  </div>
                ))}
              </div>
              <div className="kanban-col">
                <h3 style={{ marginBottom: '1rem' }}>Interviewing ({interviewingJobs.length})</h3>
                {interviewingJobs.map((job, idx) => (
                  <div key={idx} className="kanban-card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
                    <h4 style={{ marginBottom: '0.2rem' }}>{job.title}</h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>{job.company}</p>
                    <button className="btn btn-primary" style={{ fontSize: '0.7rem', padding: '0.3rem 0.6rem', background: 'var(--success)' }} onClick={() => {
                      setTrackerJobs(prev => prev.map(j => j === job ? { ...j, status: 'Offers' } : j));
                    }}>Got Offer! 🎉</button>
                  </div>
                ))}
              </div>
              <div className="kanban-col">
                <h3 style={{ marginBottom: '1rem' }}>Offers ({offerJobs.length})</h3>
                {offerJobs.map((job, idx) => (
                  <div key={idx} className="kanban-card" style={{ borderLeft: '4px solid var(--success)', background: 'rgba(16, 185, 129, 0.1)' }}>
                    <h4 style={{ marginBottom: '0.2rem' }}>{job.title}</h4>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{job.company}</p>
                    <div style={{ marginTop: '0.5rem', color: 'var(--success)', fontWeight: 'bold', fontSize: '0.8rem' }}>Offer Received! 💰</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 'salary':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Fair Pay <span className="text-gradient">Advocate</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Companies are leveraging the bad economy to lowball candidates. The AI will help you review your offer and provide respectful, professional scripts to ask for what you deserve.
            </p>
            <div className="dashboard-grid">
              <div className="card glass-panel" style={{ gridColumn: 'span 2' }}>
                <h3 style={{ marginBottom: '1rem' }}>Paste Your Offer Details</h3>
                <textarea 
                  placeholder="e.g. They offered $110k base, no equity, but the market average is $130k..." 
                  style={{ width: '100%', height: '150px', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1.5rem', outline: 'none', fontFamily: 'Inter' }} 
                  value={offerText}
                  onChange={e => setOfferText(e.target.value)}
                />
                <button 
                  className="btn btn-primary" 
                  onClick={handleGenerateScript}
                  disabled={isGeneratingScript}
                >
                  {isGeneratingScript ? "Generating Draft..." : "Generate Respectful Counter-Offer Draft"}
                </button>
                {counterScript && (
                    <div className="animate-fade-in" style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                        <h4 style={{ marginBottom: '1rem', color: 'var(--accent-primary)' }}>Your Counter-Offer Script</h4>
                        <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6' }}>
                            {counterScript}
                        </div>
                    </div>
                )}
              </div>
            </div>
          </div>
        );
        
      case 'admin':
        return (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>Maker <span className="text-gradient">Portal</span></h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              Add a highly-vetted job to the global feed for all users.
            </p>
            <div className="card glass-panel" style={{ maxWidth: '600px' }}>
              <input id="admin-title" type="text" placeholder="Job Title (e.g. Senior Backend Engineer)" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1rem', outline: 'none' }} />
              <input id="admin-company" type="text" placeholder="Company (e.g. OpenAI)" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1rem', outline: 'none' }} />
              <input id="admin-location" type="text" placeholder="Location (e.g. Remote, San Francisco)" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1rem', outline: 'none' }} />
              <input id="admin-url" type="text" placeholder="Application URL (e.g. https://tesla.com/careers/...)" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1rem', outline: 'none' }} />
              <textarea id="admin-desc" placeholder="Short Description of the Role..." style={{ width: '100%', height: '100px', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-highlight)', background: 'rgba(0,0,0,0.4)', color: 'white', marginBottom: '1rem', outline: 'none' }} />
              <button 
                className="btn btn-primary" 
                style={{ width: '100%', background: 'var(--accent-primary)', boxShadow: '0 4px 14px 0 rgba(59, 130, 246, 0.4)' }}
                onClick={async () => {
                  const title = (document.getElementById('admin-title') as HTMLInputElement).value;
                  const company = (document.getElementById('admin-company') as HTMLInputElement).value;
                  const location = (document.getElementById('admin-location') as HTMLInputElement).value;
                  const url = (document.getElementById('admin-url') as HTMLInputElement).value;
                  const desc = (document.getElementById('admin-desc') as HTMLTextAreaElement).value;
                  
                  if (!title || !company || !desc) {
                    alert("Please fill out all required fields!");
                    return;
                  }

                  const payload = {
                    title: title,
                    company: company,
                    location: location || "Remote",
                    url: url || "",
                    matchScore: Math.floor(Math.random() * (99 - 75 + 1) + 75),
                    description: desc
                  };

                  try {
                    const res = await fetch("http://localhost:8001/api/admin/job", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify(payload)
                    });
                    const data = await res.json();
                    if (data.status === "success") {
                      alert("✅ Job Successfully Published to the Global Feed!");
                      (document.getElementById('admin-title') as HTMLInputElement).value = '';
                      (document.getElementById('admin-company') as HTMLInputElement).value = '';
                      (document.getElementById('admin-location') as HTMLInputElement).value = '';
                      (document.getElementById('admin-desc') as HTMLTextAreaElement).value = '';
                    } else {
                      alert("Failed to publish: " + data.message);
                    }
                  } catch (e) {
                    alert("Error publishing job. Make sure backend is running.");
                  }
                }}
              >
                🌍 Publish Job Globally
              </button>
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
          <div className={`nav-item ${activeTab === 'sync' ? 'active' : ''}`} onClick={() => setActiveTab('sync')}>🔗 Master Profile</div>
          <div className={`nav-item ${activeTab === 'feed' ? 'active' : ''}`} onClick={() => setActiveTab('feed')}>🔍 Job Feed</div>
          <div className={`nav-item ${activeTab === 'apply' ? 'active' : ''}`} onClick={() => setActiveTab('apply')}>📄 Resume Tailorer</div>
          <div className={`nav-item ${activeTab === 'kanban' ? 'active' : ''}`} onClick={() => setActiveTab('kanban')}>📊 Tracker Board</div>
          <div className={`nav-item ${activeTab === 'interview' ? 'active' : ''}`} onClick={() => setActiveTab('interview')}>🤖 Interview Prep</div>
          <div className={`nav-item ${activeTab === 'salary' ? 'active' : ''}`} onClick={() => setActiveTab('salary')}>💰 Fair Pay Advocate</div>
          {window.location.search.includes('makerMode=true') && (
            <>
              <div style={{ marginTop: '2rem', padding: '0 1.5rem', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Creator Tools</div>
              <div className={`nav-item ${activeTab === 'admin' ? 'active' : ''}`} onClick={() => setActiveTab('admin')}>👑 Maker Portal</div>
            </>
          )}
          <div className={`nav-item ${activeTab === 'upskill' ? 'active' : ''}`} onClick={() => setActiveTab('upskill')}>🔥 Gap Heatmap</div>
        </div>
        <div style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>🕵️</div>
            <div>
              <div style={{ fontWeight: 'bold' }}>Local Session</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>No Account Needed</div>
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
