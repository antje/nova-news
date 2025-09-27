"use client";
import { useEffect, useRef, useState } from "react";
import cx from "classnames";
import Link from "next/link";

type Article = {
  title: string;
  summary: string;
  url: string;
  source: string;
};

type NewsSite = {
  id: number;
  name: string;
  code: string;
  url: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

type SiteSelectorProps = {
  availableSites: NewsSite[];
  selectedSites: Set<string>;
  onSelectionChange: (newSelection: Set<string>) => void;
  hasError: boolean;
};

function SiteSelector({ availableSites, selectedSites, onSelectionChange, hasError }: SiteSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  
  const selectedCount = selectedSites.size;
  const totalCount = availableSites.length;
  
  const toggleSite = (siteCode: string) => {
    const newSelected = new Set(selectedSites);
    if (newSelected.has(siteCode)) {
      newSelected.delete(siteCode);
    } else {
      newSelected.add(siteCode);
    }
    onSelectionChange(newSelected);
  };
  
  const selectAll = () => {
    const allSites = new Set(availableSites.map(site => site.code));
    onSelectionChange(allSites);
  };
  
  const selectNone = () => {
    onSelectionChange(new Set());
  };
  
  const getDisplayText = () => {
    if (selectedCount === 0) return "Select news sites";
    if (selectedCount === totalCount) return `All sites (${totalCount})`;
    if (selectedCount === 1) {
      const selectedSite = availableSites.find(site => selectedSites.has(site.code));
      return selectedSite?.name || "1 site";
    }
    return `${selectedCount} sites selected`;
  };
  
  return (
    <div style={{ position: "relative", minWidth: "200px", zIndex: isOpen ? 9999 : 1 }}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          background: "#10162B",
          border: hasError ? "1px solid #7A1F2B" : "1px solid #1C2744",
          color: selectedCount === 0 ? "#8B92A6" : "#E6EAF2",
          padding: "12px 14px",
          borderRadius: 8,
          cursor: "pointer",
          fontSize: 14,
          fontWeight: selectedCount > 0 ? 500 : 400,
          outline: "none",
          transition: "all 0.2s ease",
        }}
        onMouseEnter={(e) => {
          if (!hasError) {
            e.currentTarget.style.borderColor = "#4C7CF8";
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = hasError ? "#7A1F2B" : "#1C2744";
        }}
      >
        <span>{getDisplayText()}</span>
        <span style={{ 
          transform: isOpen ? "rotate(180deg)" : "rotate(0deg)", 
          transition: "transform 0.2s ease",
          marginLeft: 8,
          opacity: 0.7
        }}>
          ▼
        </span>
      </button>
      
      {isOpen && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            width: "250px",
            marginTop: 4,
            background: "#0F1527",
            border: "1px solid #1C2744",
            borderRadius: 8,
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
            zIndex: 10000,
            maxHeight: "300px",
            overflowY: "auto",
          }}
        >
          {/* Header with Select All/None */}
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "12px 14px",
            borderBottom: "1px solid #1C2744",
            background: "#1A1F3A",
          }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "#8B92A6", textTransform: "uppercase" }}>
              News Sites
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                type="button"
                onClick={selectAll}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#4C7CF8",
                  fontSize: 11,
                  cursor: "pointer",
                  padding: "2px 6px",
                  borderRadius: 4,
                  fontWeight: 500,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#1A2B4C";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                }}
              >
                All
              </button>
              <button
                type="button"
                onClick={selectNone}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#8B92A6",
                  fontSize: 11,
                  cursor: "pointer",
                  padding: "2px 6px",
                  borderRadius: 4,
                  fontWeight: 500,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#1A1A1A";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                }}
              >
                None
              </button>
            </div>
          </div>
          
          {/* Site List */}
          {availableSites.map((site) => {
            const isSelected = selectedSites.has(site.code);
            return (
              <div
                key={site.code}
                onClick={() => toggleSite(site.code)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 14px",
                  cursor: "pointer",
                  transition: "background 0.15s ease",
                  borderBottom: "1px solid #1A1F3A",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#151A31";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                }}
              >
                <div
                  style={{
                    width: 16,
                    height: 16,
                    borderRadius: 3,
                    border: isSelected ? "2px solid #4C7CF8" : "2px solid #3A4553",
                    background: isSelected ? "#4C7CF8" : "transparent",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "all 0.2s ease",
                  }}
                >
                  {isSelected && (
                    <span style={{ color: "white", fontSize: 10, fontWeight: "bold" }}>✓</span>
                  )}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    color: isSelected ? "#E6EAF2" : "#B8BCC8", 
                    fontSize: 14, 
                    fontWeight: isSelected ? 500 : 400,
                    marginBottom: 2
                  }}>
                    {site.name}
                  </div>
                  {site.is_default && (
                    <div style={{ 
                      fontSize: 11, 
                      color: "#8B92A6",
                      fontStyle: "italic"
                    }}>
                      Default site
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      {/* Click outside to close */}
      {isOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 9998,
          }}
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}

export default function HomePage() {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [articles, setArticles] = useState<Article[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [availableSites, setAvailableSites] = useState<NewsSite[]>([]);
  const [selectedSites, setSelectedSites] = useState<Set<string>>(new Set());
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<"idle" | "queued" | "running" | "completed" | "failed">("idle");
  const [logs, setLogs] = useState<string[]>([]);
  const lastLogIndexRef = useRef<number>(0);
  const wsRef = useRef<WebSocket | null>(null);
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<"unknown" | "available" | "unavailable">("unknown");

  // Function to load job results from a previous search
  const loadJobResults = async (jobId: string, urlTopic: string, urlSites: string | null, sites: NewsSite[]) => {
    try {
      setLoading(true);
      setError(null);
      setArticles([]);
      setJobStatus("completed");
      setJobId(jobId);

      // Fetch the job results
      const response = await fetch(`${API_BASE}/api/search_jobs/${jobId}/results`);
      if (!response.ok) {
        throw new Error(`Failed to load search results: ${response.status}`);
      }

      const data = await response.json();
      
      // Handle response format
      let items: Article[];
      if (Array.isArray(data)) {
        items = data;
      } else if (data?.results && Array.isArray(data.results)) {
        items = data.results;
      } else {
        console.warn("Unexpected results format:", data);
        items = [];
      }

      setArticles(items);
      setLastJobId(jobId);

      // Set up sites selection if provided
      if (urlSites && sites.length > 0) {
        const sitesList = urlSites.split(',').map(s => s.trim()).filter(s => s);
        // Only select sites that exist in available sites
        const validSites = sitesList.filter(siteCode => 
          sites.some(site => site.code === siteCode)
        );
        if (validSites.length > 0) {
          setSelectedSites(new Set(validSites));
        }
      }

      console.log(`Loaded ${items.length} articles from previous search`);
    } catch (err: any) {
      console.error("Error loading job results:", err);
      setError(err?.message || "Failed to load previous search results");
    } finally {
      setLoading(false);
    }
  };

  // Load last job ID from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('novanews-last-job-id');
    if (saved) {
      setLastJobId(saved);
    }
  }, []);

  // Load available sites and setup health check
  useEffect(() => {
    const loadSites = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/sites?active_only=true`);
        if (response.ok) {
          const sites = await response.json();
          setAvailableSites(sites);
          // Set default sites as selected
          const defaultSites = new Set<string>(sites.filter((site: NewsSite) => site.is_default).map((site: NewsSite) => site.code));
          setSelectedSites(defaultSites);
        }
      } catch (err) {
        console.error("Failed to load sites:", err);
        // Fallback to hardcoded sites if loading fails
        setAvailableSites([
          { id: 1, name: "Latent Space", code: "latent_space", url: "https://www.latent.space/", is_active: true, is_default: true, created_at: "", updated_at: "" }
        ]);
        setSelectedSites(new Set(["latent_space"]));
      }
    };

    const checkApiHealth = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/health`, { 
          signal: AbortSignal.timeout(3000) 
        });
        setApiStatus(response.ok ? "available" : "unavailable");
      } catch {
        setApiStatus("unavailable");
      }
    };

    // Load sites and check health immediately
    loadSites();
    
    checkApiHealth();
    
    // Check health every 10 seconds
    const interval = setInterval(checkApiHealth, 10000);
    
    return () => clearInterval(interval);
  }, []);

  // Check for URL parameters to load a previous search when sites are available
  useEffect(() => {
    if (availableSites.length > 0) {
      const urlParams = new URLSearchParams(window.location.search);
      const jobId = urlParams.get('jobId');
      const urlTopic = urlParams.get('topic');
      const urlSites = urlParams.get('sites');

      if (jobId && urlTopic) {
        // Set the form values
        setTopic(urlTopic);
        
        // Load the job results
        loadJobResults(jobId, urlTopic, urlSites, availableSites);
        
        // Clear URL parameters to avoid reloading on refresh
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    }
  }, [availableSites]);

  // Save last job ID to localStorage when it changes
  useEffect(() => {
    if (lastJobId) {
      localStorage.setItem('novanews-last-job-id', lastJobId);
    }
  }, [lastJobId]);


  useEffect(() => {
    return () => {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch {}
      }
    };
  }, []);

  const onSearch = async () => {
    setLoading(true);
    setError(null);
    setArticles([]);
    setLogs([]);
    setJobId(null);
    setJobStatus("idle");
    try {
      // require topic
      if (!topic || topic.trim().length === 0) {
        setError("Please enter a topic");
        setLoading(false);
        return;
      }
      // require at least one site
      const selected = Array.from(selectedSites);
      if (selected.length === 0) {
        setError("Please select at least one site");
        setLoading(false);
        return;
      }
      const payload = { topic, max_items_per_site: 3, sites: selected.join(",") };
      const res = await fetch(`${API_BASE}/api/search_jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const job = await res.json();
      if (!job?.job_id) throw new Error("Invalid job response");
      setJobId(job.job_id);
      setLastJobId(job.job_id);
      setJobStatus((job.status as any) || "queued");

      // connect websocket for live logs and job management
      const wsUrl = API_BASE.replace(/^http/, "ws") + `/ws/logs/${job.job_id}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onmessage = (ev) => {
        try {
          const message = JSON.parse(ev.data);
          console.log("WebSocket message:", message);
          
          switch (message.type) {
            case "log": {
              // Support both legacy string and new { message, line_number }
              const payload = message.data;
              if (payload && typeof payload === "object" && typeof payload.line_number === "number") {
                const idx = payload.line_number as number;
                const text = String(payload.message || "");
                if (idx > lastLogIndexRef.current) {
                  lastLogIndexRef.current = idx;
                  setLogs((prev) => [...prev, text]);
                }
              } else {
                const text = String(payload || "");
                setLogs((prev) => {
                  if (prev.length > 0 && prev[prev.length - 1] === text) return prev;
                  return [...prev, text];
                });
              }
              break;
            }
              
            case "status":
              if (message.data?.status) {
                setJobStatus(message.data.status);
                console.log(`Job ${job.job_id} status updated:`, message.data.status);
                
                // Clear loading state when job completes
                if (message.data.status === "completed" || message.data.status === "failed") {
                  setLoading(false);
                }
              }
              if (message.data?.error) {
                setError(message.data.error);
              }
              break;
              
            case "results":
              try {
                // Handle both possible response formats
                let items: Article[];
                if (Array.isArray(message.data)) {
                  items = message.data;
                } else if (message.data?.results && Array.isArray(message.data.results)) {
                  items = message.data.results;
                } else {
                  console.warn("Unexpected results format:", message.data);
                  items = [];
                }
                
                setArticles(items);
                console.log(`Successfully loaded ${items.length} articles from WebSocket`);
              } catch (resultsError) {
                console.error("Error processing results:", resultsError);
                setError(`Error processing results: ${resultsError}`);
              }
              break;
              
            case "error":
              setError(String(message.data || "Unknown error"));
              setJobStatus("failed");
              setLoading(false);
              break;
              
            case "complete":
              console.log("Job completed:", message.data);
              setLoading(false);
              
              // Update job status based on final status
              if (message.data?.final_status) {
                setJobStatus(message.data.final_status);
              }
              // After completion, fetch latest logs to ensure any final messages are displayed
              if (job.job_id) {
                try {
                  fetch(`${API_BASE}/api/search_jobs/${job.job_id}/logs?from_index=0`)
                    .then((res) => res.ok ? res.json() : [])
                    .then((serverLogs) => {
                      if (Array.isArray(serverLogs)) {
                        setLogs(serverLogs);
                      }
                    })
                    .catch(() => {});
                } catch {}
              }
              // WebSocket will close automatically
              break;
              
            default:
              console.warn("Unknown WebSocket message type:", message.type);
          }
        } catch (parseError) {
          // Fallback for non-JSON messages (legacy compatibility)
          console.warn("Failed to parse WebSocket message as JSON, treating as log:", parseError);
          const messageText = String(ev.data || "");
          setLogs((prev) => {
            if (prev.length > 0 && prev[prev.length - 1] === messageText) return prev;
            return [...prev, messageText];
          });
          
          // If the message contains error indicators, treat it as a job failure
          if (messageText.toLowerCase().includes("error") || 
              messageText.toLowerCase().includes("failed") ||
              messageText.toLowerCase().includes("exception")) {
            setJobStatus("failed");
            setLoading(false);
          }
        }
      };
      
      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setError("Connection error - please try again");
        setJobStatus("failed");
        setLoading(false);
      };
      
      ws.onclose = (event) => {
        console.log("WebSocket closed:", event.code, event.reason);
        wsRef.current = null;
        
        // Always clear loading state when WebSocket closes
        // The job status will be preserved to show the final state
        setLoading(false);
        
        // Only show connection error if the job was still running and connection wasn't clean
        if ((jobStatus === "running" || jobStatus === "queued") && !event.wasClean) {
          setError("Connection lost - please try again");
        }
      };
    } catch (e: any) {
      setError(e?.message ?? "Failed to fetch results");
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 960, margin: "40px auto", padding: "0 20px" }}>
      <header style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <img src="/nova-act.svg" alt="Nova Act" width={28} height={28} style={{ display: "block" }} />
            <h1 style={{ margin: 0, fontSize: 28 }}>NovaNews</h1>
            {apiStatus !== "unknown" && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "4px 8px",
                borderRadius: 12,
                fontSize: 12,
                fontWeight: 500,
                background: apiStatus === "available" ? "#1E3A2A" : "#3A1E1E",
                color: apiStatus === "available" ? "#B8FFCE" : "#FFB8B8",
                border: `1px solid ${apiStatus === "available" ? "#3B5B47" : "#5B3B3B"}`
              }}>
                <div style={{ 
                  width: 6, 
                  height: 6, 
                  borderRadius: "50%", 
                  background: apiStatus === "available" ? "#4AE54A" : "#E54A4A" 
                }} />
                API {apiStatus === "available" ? "Online" : "Offline"}
              </div>
            )}
          </div>
          <Link href="/admin" style={{
            textDecoration: "none",
            color: "#4C7CF8",
            fontSize: 14,
            fontWeight: 500,
            padding: "8px 12px",
            border: "1px solid #4C7CF8",
            borderRadius: 6,
            transition: "all 0.2s ease"
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#4C7CF8";
            e.currentTarget.style.color = "white";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = "#4C7CF8";
          }}>
            Admin Dashboard
          </Link>
        </div>
        <p style={{ opacity: 0.8 }}>
          Search AI news outlets for topic-related posts.
        </p>
      </header>
      {error && (
        <div role="alert" aria-live="assertive" style={{ background: "#2B1431", border: "1px solid #6B1C3D", padding: 12, borderRadius: 8, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* Search Form Section */}
      <section style={{ display: "flex", gap: 24, marginBottom: 24, alignItems: "center", flexWrap: "wrap" }}>
          {(() => {
            const topicEmpty = !topic.trim();
            const noneSelected = selectedSites.size === 0;
            return (
              <>
                <div style={{ flex: "0 1 350px", minWidth: "280px" }}>
                  <input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Enter a topic (e.g. nova act)"
                    style={{
                      width: "100%",
                      background: "#10162B",
                      border: topicEmpty ? "1px solid #7A1F2B" : "1px solid #1C2744",
                      color: "#E6EAF2",
                      padding: "12px 14px",
                      borderRadius: 8,
                      outline: "none",
                      fontSize: 14,
                    }}
                  />
                </div>
                
                <SiteSelector 
                  availableSites={availableSites}
                  selectedSites={selectedSites}
                  onSelectionChange={setSelectedSites}
                  hasError={noneSelected}
                />
                
                <button
                  onClick={onSearch}
                  disabled={loading || topicEmpty || noneSelected || apiStatus === "unavailable"}
                  style={{
                    background: loading || apiStatus === "unavailable" ? "#2B3658" : "#4C7CF8",
                    border: 0,
                    color: "white",
                    padding: "12px 16px",
                    borderRadius: 8,
                    cursor: loading || apiStatus === "unavailable" ? "default" : "pointer",
                    fontWeight: 600,
                    opacity: apiStatus === "unavailable" ? 0.6 : 1,
                    whiteSpace: "nowrap",
                  }}
                  title={apiStatus === "unavailable" ? "API server is offline" : ""}
                >
                  {loading ? (jobStatus === "running" || jobStatus === "queued" ? "Searching... (live logs)" : "Searching...") : "Search"}
                </button>
              </>
            );
          })()}
      </section>

      {/* Inline validation messages */}
      <section aria-live="polite" style={{ marginTop: 16, marginBottom: 24 }}>
        {!topic.trim() && (
          <div style={{ color: "#FF90A3", fontSize: 13, marginTop: 4 }}>Please enter a topic.</div>
        )}
        {selectedSites.size === 0 && (
          <div style={{ color: "#FF90A3", fontSize: 13, marginTop: 4 }}>Please select at least one site.</div>
        )}
        {apiStatus === "unavailable" && (
          <div style={{ color: "#FF90A3", fontSize: 13, marginTop: 4 }}>
            ⚠️ API server is offline. Please start the backend server to search.
          </div>
        )}
      </section>

      {logs.length > 0 || (loading && (jobId || jobStatus === "queued" || jobStatus === "running")) ? (
        <section style={{ marginBottom: 16 }}>
          <div style={{ marginBottom: 6, fontWeight: 600 }}>Live logs{jobStatus ? ` — ${jobStatus}` : ""}</div>
          <div style={{ background: "#0F1527", border: "1px solid #1C2744", borderRadius: 10, padding: 12, maxHeight: 220, overflow: "auto", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 12, lineHeight: 1.4 }}>
            {logs.length === 0 ? (
              <div style={{ opacity: 0.7 }}>Waiting for logs...</div>
            ) : (
              logs.map((line, i) => (
                <div key={i} style={{ whiteSpace: "pre-wrap" }}>{line}</div>
              ))
            )}
          </div>
        </section>
      ) : null}

      {/* Search Results Widget */}
      <section style={{ marginTop: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>
            Search Results {articles.length > 0 && `(${articles.length})`}
          </h2>
        </div>

        {articles.length === 0 ? (
          <div style={{ 
            background: "#0F1527", 
            border: "2px dashed #1C2744", 
            borderRadius: 12, 
            padding: 32, 
            textAlign: "center",
            color: "#8B92A6" 
          }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>
              🔍
            </div>
            <div style={{ fontSize: 16, marginBottom: 8, fontWeight: 500 }}>
              No search results yet
            </div>
            <div style={{ fontSize: 14, opacity: 0.8 }}>
              {loading 
                ? "Search in progress..." 
                : "Try searching for a topic above"
              }
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gap: 16 }}>
            {articles.map((article, idx) => (
              <div
                key={idx}
                style={{
                  background: "linear-gradient(135deg, #0F1527 0%, #1A1F3A 100%)",
                  border: "1px solid #2A3441",
                  borderRadius: 12,
                  padding: 20,
                  transition: "all 0.2s ease",
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "#4C7CF8";
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 8px 32px rgba(76, 124, 248, 0.15)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "#2A3441";
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "none";
                }}
                onClick={() => window.open(article.url, "_blank", "noopener,noreferrer")}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: 16, marginBottom: 12 }}>
                  <div style={{ flex: 1 }}>
                    <h3 style={{ 
                      margin: 0, 
                      fontSize: 18, 
                      fontWeight: 600, 
                      color: "#E6EAF2", 
                      lineHeight: 1.3,
                      marginBottom: 8
                    }}>
                      {article.title}
                    </h3>
                  </div>
                  <div
                    style={{
                      background: (() => {
                        const site = availableSites.find(s => s.code === article.source);
                        // Generate a color based on the site name hash
                        if (!site) return "linear-gradient(135deg, #2A2A2A 0%, #3A3A3A 100%)";
                        const hash = site.name.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a; }, 0);
                        const hue = Math.abs(hash) % 360;
                        return `linear-gradient(135deg, hsl(${hue}, 40%, 20%) 0%, hsl(${hue}, 45%, 25%) 100%)`;
                      })(),
                      color: (() => {
                        const site = availableSites.find(s => s.code === article.source);
                        if (!site) return "#B8BCC8";
                        const hash = site.name.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a; }, 0);
                        const hue = Math.abs(hash) % 360;
                        return `hsl(${hue}, 60%, 80%)`;
                      })(),
                      border: (() => {
                        const site = availableSites.find(s => s.code === article.source);
                        if (!site) return "1px solid #4A4A4A";
                        const hash = site.name.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a; }, 0);
                        const hue = Math.abs(hash) % 360;
                        return `1px solid hsl(${hue}, 45%, 35%)`;
                      })(),
                      padding: "6px 12px",
                      borderRadius: 20,
                      fontSize: 12,
                      fontWeight: 600,
                      textTransform: "uppercase",
                      letterSpacing: "0.5px",
                      whiteSpace: "nowrap",
                      boxShadow: (() => {
                        const site = availableSites.find(s => s.code === article.source);
                        if (!site) return "0 2px 8px rgba(184, 188, 200, 0.2)";
                        const hash = site.name.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a; }, 0);
                        const hue = Math.abs(hash) % 360;
                        return `0 2px 8px hsla(${hue}, 60%, 80%, 0.2)`;
                      })(),
                    }}
                  >
                    {availableSites.find(s => s.code === article.source)?.name || article.source}
                  </div>
                </div>
                
                <p style={{ 
                  margin: 0, 
                  color: "#B8BCC8", 
                  lineHeight: 1.5, 
                  fontSize: 14
                }}>
                  {article.summary}
                </p>
                
                <div style={{ 
                  marginTop: 16, 
                  paddingTop: 16, 
                  borderTop: "1px solid #2A3441",
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  color: "#8B92A6",
                  fontSize: 12
                }}>
                  <span>🔗</span>
                  <span style={{ 
                    color: "#4C7CF8", 
                    textDecoration: "none",
                    fontWeight: 500
                  }}>
                    Click to read full article
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}


