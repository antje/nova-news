"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

type AdminSearchJob = {
  job_id: string;
  topic: string;
  sites: string | null;
  max_items_per_site: number;
  status: string;
  created_at: string;
  updated_at: string;
  error: string | null;
  result_count: number;
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

export default function AdminPage() {
  const [jobs, setJobs] = useState<AdminSearchJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Sites management state
  const [sites, setSites] = useState<NewsSite[]>([]);
  const [sitesLoading, setSitesLoading] = useState(true);
  const [sitesError, setSitesError] = useState<string | null>(null);
  const [showAddSite, setShowAddSite] = useState(false);
  const [newSiteName, setNewSiteName] = useState("");
  const [newSiteCode, setNewSiteCode] = useState("");
  const [newSiteUrl, setNewSiteUrl] = useState("");
  const [submittingSite, setSubmittingSite] = useState(false);
  
  // Edit mode state
  const [editingSiteId, setEditingSiteId] = useState<number | null>(null);
  const [editFormData, setEditFormData] = useState({ name: "", code: "", url: "" });
  const [updatingSite, setUpdatingSite] = useState(false);
  
  // Job deletion state
  const [deletingJobId, setDeletingJobId] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/admin/search_jobs`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        setJobs(data);
      } catch (err: any) {
        setError(err?.message || "Failed to fetch search jobs");
      } finally {
        setLoading(false);
      }
    };

    const fetchSites = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/admin/sites`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        setSites(data);
      } catch (err: any) {
        setSitesError(err?.message || "Failed to fetch news sites");
      } finally {
        setSitesLoading(false);
      }
    };

    fetchJobs();
    fetchSites();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return { bg: "#1E3A2A", color: "#B8FFCE", border: "#3B5B47" };
      case "running":
        return { bg: "#2A2E1E", color: "#FFFFC6", border: "#5B5F3B" };
      case "failed":
        return { bg: "#3A1E1E", color: "#FFB8B8", border: "#5B3B3B" };
      case "queued":
        return { bg: "#1E2A3A", color: "#C6E5FF", border: "#3B475B" };
      default:
        return { bg: "#2A2A2A", color: "#E6EAF2", border: "#4A4A4A" };
    }
  };

  const formatSites = (sites: string | null) => {
    if (!sites) return "latent_space, forward_future";
    return sites.split(",").map(site => site.trim()).join(", ");
  };

  const handleAddSite = async () => {
    if (!newSiteName.trim() || !newSiteCode.trim() || !newSiteUrl.trim()) {
      setSitesError("Please fill in all fields");
      return;
    }

    setSubmittingSite(true);
    setSitesError(null);

    try {
      const response = await fetch(`${API_BASE}/api/admin/sites`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newSiteName.trim(),
          code: newSiteCode.trim(),
          url: newSiteUrl.trim(),
          is_active: true
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const newSite = await response.json();
      setSites(prev => [...prev, newSite]);
      setNewSiteName("");
      setNewSiteCode("");
      setNewSiteUrl("");
      setShowAddSite(false);
    } catch (err: any) {
      setSitesError(err?.message || "Failed to add site");
    } finally {
      setSubmittingSite(false);
    }
  };

  const handleDeleteSite = async (siteId: number, siteName: string) => {
    if (!confirm(`Are you sure you want to delete "${siteName}"?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/admin/sites/${siteId}`, {
        method: "DELETE"
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      setSites(prev => prev.filter(site => site.id !== siteId));
    } catch (err: any) {
      setSitesError(err?.message || "Failed to delete site");
    }
  };

  const handleToggleSiteActive = async (siteId: number, currentActive: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/sites/${siteId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: !currentActive })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const updatedSite = await response.json();
      setSites(prev => prev.map(site => site.id === siteId ? updatedSite : site));
    } catch (err: any) {
      setSitesError(err?.message || "Failed to update site");
    }
  };

  const handleToggleSiteDefault = async (siteId: number, currentDefault: boolean) => {
    try {
      // Check if this would leave no default sites
      if (currentDefault) {
        const defaultCount = sites.filter(site => site.is_default).length;
        if (defaultCount <= 1) {
          setSitesError("At least one site must be set as default");
          return;
        }
      }

      const response = await fetch(`${API_BASE}/api/admin/sites/${siteId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_default: !currentDefault })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const updatedSite = await response.json();
      setSites(prev => prev.map(site => site.id === siteId ? updatedSite : site));
      setSitesError(null); // Clear any previous errors
    } catch (err: any) {
      setSitesError(err?.message || "Failed to update site default status");
    }
  };

  const handleEditSite = (site: NewsSite) => {
    setEditingSiteId(site.id);
    setEditFormData({
      name: site.name,
      code: site.code,
      url: site.url
    });
    setSitesError(null);
  };

  const handleCancelEdit = () => {
    setEditingSiteId(null);
    setEditFormData({ name: "", code: "", url: "" });
    setSitesError(null);
  };

  const handleSaveEdit = async () => {
    if (!editingSiteId) return;

    if (!editFormData.name.trim() || !editFormData.code.trim() || !editFormData.url.trim()) {
      setSitesError("Please fill in all fields");
      return;
    }

    setUpdatingSite(true);
    setSitesError(null);

    try {
      const response = await fetch(`${API_BASE}/api/admin/sites/${editingSiteId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: editFormData.name.trim(),
          code: editFormData.code.trim(),
          url: editFormData.url.trim()
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      const updatedSite = await response.json();
      setSites(prev => prev.map(site => site.id === editingSiteId ? updatedSite : site));
      setEditingSiteId(null);
      setEditFormData({ name: "", code: "", url: "" });
    } catch (err: any) {
      setSitesError(err?.message || "Failed to update site");
    } finally {
      setUpdatingSite(false);
    }
  };

  const handleDeleteJob = async (jobId: string, topic: string) => {
    if (!confirm(`Are you sure you want to delete the search job for "${topic}"?`)) {
      return;
    }

    setDeletingJobId(jobId);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/admin/search_jobs/${jobId}`, {
        method: "DELETE"
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      // Remove the job from the list
      setJobs(prev => prev.filter(job => job.job_id !== jobId));
    } catch (err: any) {
      setError(err?.message || "Failed to delete job");
    } finally {
      setDeletingJobId(null);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: "40px auto", padding: "0 20px" }}>
      <header style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 8 }}>
          <Link href="/" style={{ 
            textDecoration: "none", 
            color: "#4C7CF8", 
            fontSize: 14,
            fontWeight: 500,
            display: "flex",
            alignItems: "center",
            gap: 6
          }}>
            ← Back to Search
          </Link>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <img src="/nova-act.svg" alt="Nova Act" width={28} height={28} style={{ display: "block" }} />
          <h1 style={{ margin: 0, fontSize: 28 }}>NovaNews Admin</h1>
        </div>
        <p style={{ opacity: 0.8, marginTop: 8 }}>
          View all search jobs and configure news site defaults.
        </p>
      </header>

      {/* Search Jobs Section */}
      <section style={{ marginBottom: 32 }}>
        <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600, marginBottom: 8 }}>View search jobs</h2>
        <p style={{ margin: 0, fontSize: 14, opacity: 0.8, marginBottom: 24 }}>
          Monitor all search job statuses and results.
        </p>
      </section>

      {error && (
        <div role="alert" aria-live="assertive" style={{ 
          background: "#2B1431", 
          border: "1px solid #6B1C3D", 
          padding: 16, 
          borderRadius: 8, 
          marginBottom: 24 
        }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ 
          display: "flex", 
          justifyContent: "center", 
          alignItems: "center", 
          padding: 64,
          color: "#8B92A6" 
        }}>
          Loading search jobs...
        </div>
      ) : jobs.length === 0 ? (
        <div style={{ 
          background: "#0F1527", 
          border: "2px dashed #1C2744", 
          borderRadius: 12, 
          padding: 48, 
          textAlign: "center",
          color: "#8B92A6" 
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
          <div style={{ fontSize: 18, marginBottom: 8, fontWeight: 500 }}>
            No search jobs found
          </div>
          <div style={{ fontSize: 14, opacity: 0.8 }}>
            Search jobs will appear here once they are created.
          </div>
        </div>
      ) : (
        <div style={{ 
          background: "#0F1527", 
          border: "1px solid #1C2744", 
          borderRadius: 12, 
          overflow: "hidden" 
        }}>
          <div style={{ 
            display: "grid", 
            gridTemplateColumns: "2fr 1fr 80px 80px 100px 140px 80px",
            gap: 16,
            padding: "16px 20px",
            background: "#1A1F3A",
            borderBottom: "1px solid #1C2744",
            fontSize: 12,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            color: "#8B92A6"
          }}>
            <div>Topic</div>
            <div>Sites</div>
            <div>Max/Site</div>
            <div>Results</div>
            <div>Status</div>
            <div>Created</div>
            <div>Actions</div>
          </div>
          
          {jobs.map((job, idx) => {
            const statusStyle = getStatusColor(job.status);
            const isClickable = job.status === "completed" && job.result_count > 0;
            
            const handleJobClick = () => {
              if (isClickable) {
                // Navigate to main page with job parameters
                const params = new URLSearchParams({
                  jobId: job.job_id,
                  topic: job.topic,
                  sites: job.sites || ""
                });
                window.location.href = `/?${params.toString()}`;
              }
            };

            const getTooltipMessage = () => {
              if (job.status === "completed" && job.result_count > 0) {
                return `Click to load this search (${job.result_count} results found)`;
              } else if (job.status === "failed") {
                return "Search failed - cannot load results";
              } else if (job.status === "running") {
                return "Search still in progress - cannot load yet";
              } else if (job.status === "queued") {
                return "Search queued - cannot load yet";
              } else if (job.status === "completed" && job.result_count === 0) {
                return "No results found - nothing to load";
              } else {
                return `Status: ${job.status}`;
              }
            };
            
            return (
              <div 
                key={job.job_id}
                style={{ 
                  display: "grid", 
                  gridTemplateColumns: "2fr 1fr 80px 80px 100px 140px 80px",
                  gap: 16,
                  padding: "16px 20px",
                  borderBottom: idx < jobs.length - 1 ? "1px solid #1C2744" : "none",
                  transition: "all 0.2s ease",
                  cursor: isClickable ? "pointer" : "default",
                  opacity: isClickable ? 1 : 0.7
                }}
                onClick={handleJobClick}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = isClickable ? "#1A2B4C" : "#151A31";
                  e.currentTarget.style.opacity = isClickable ? "1" : "0.85";
                  if (isClickable) {
                    e.currentTarget.style.transform = "translateY(-1px)";
                    e.currentTarget.style.boxShadow = "0 4px 16px rgba(76, 124, 248, 0.1)";
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "none";
                  e.currentTarget.style.opacity = isClickable ? "1" : "0.7";
                }}
                title={getTooltipMessage()}
              >
                <div style={{ 
                  fontWeight: 500,
                  color: "#E6EAF2",
                  wordBreak: "break-word",
                  display: "flex",
                  alignItems: "center",
                  gap: 8
                }}>
                  {job.topic}
                  {isClickable ? (
                    <span style={{ 
                      color: "#4C7CF8", 
                      fontSize: 12,
                      opacity: 0.8
                    }}>
                      ↗
                    </span>
                  ) : (
                    <span style={{ 
                      color: "#6B7280", 
                      fontSize: 10,
                      opacity: 0.6,
                      marginLeft: 4
                    }}>
                      {job.status === "failed" ? "✗" : 
                       job.status === "running" || job.status === "queued" ? "⏳" :
                       job.status === "completed" && job.result_count === 0 ? "∅" : "–"}
                    </span>
                  )}
                </div>
                
                <div style={{ 
                  fontSize: 12,
                  color: "#B8BCC8",
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
                }}>
                  {formatSites(job.sites)}
                </div>
                
                <div style={{ 
                  fontSize: 14,
                  color: "#8B92A6",
                  textAlign: "center"
                }}>
                  {job.max_items_per_site}
                </div>
                
                <div style={{ 
                  fontSize: 16,
                  fontWeight: 600,
                  color: job.result_count > 0 ? "#B8FFCE" : "#8B92A6",
                  textAlign: "center"
                }}>
                  {job.result_count}
                </div>
                
                <div style={{ display: "flex", justifyContent: "center" }}>
                  <span style={{
                    background: statusStyle.bg,
                    color: statusStyle.color,
                    border: `1px solid ${statusStyle.border}`,
                    padding: "4px 8px",
                    borderRadius: 12,
                    fontSize: 10,
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px"
                  }}>
                    {job.status}
                  </span>
                </div>
                
                <div style={{ 
                  fontSize: 11,
                  color: "#8B92A6",
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
                }}>
                  {formatDate(job.created_at)}
                </div>
                
                {/* Actions Column */}
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
                  {job.status !== "running" && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent triggering job click
                        handleDeleteJob(job.job_id, job.topic);
                      }}
                      disabled={deletingJobId === job.job_id}
                      style={{
                        background: "transparent",
                        border: "1px solid #5B3B3B",
                        color: deletingJobId === job.job_id ? "#6B7280" : "#FFB8B8",
                        padding: "4px 8px",
                        borderRadius: 4,
                        fontSize: 16,
                        cursor: deletingJobId === job.job_id ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        opacity: deletingJobId === job.job_id ? 0.5 : 1,
                        transition: "all 0.2s ease"
                      }}
                      onMouseEnter={(e) => {
                        if (deletingJobId !== job.job_id) {
                          e.currentTarget.style.background = "#3A1E1E";
                          e.currentTarget.style.borderColor = "#FFB8B8";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (deletingJobId !== job.job_id) {
                          e.currentTarget.style.background = "transparent";
                          e.currentTarget.style.borderColor = "#5B3B3B";
                        }
                      }}
                      title={deletingJobId === job.job_id ? "Deleting..." : "Delete job"}
                    >
                      {deletingJobId === job.job_id ? "..." : "🗑️"}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ 
        marginTop: 24, 
        padding: 16, 
        background: "#0F1527", 
        border: "1px solid #1C2744", 
        borderRadius: 8,
        fontSize: 12,
        color: "#8B92A6"
      }}>
        <strong style={{ color: "#E6EAF2" }}>Total Jobs:</strong> {jobs.length}
        {jobs.length > 0 && (
          <>
            {" • "}
            <strong style={{ color: "#E6EAF2" }}>Completed:</strong> {jobs.filter(j => j.status === "completed").length}
            {" • "}
            <strong style={{ color: "#E6EAF2" }}>Total Results:</strong> {jobs.reduce((sum, j) => sum + j.result_count, 0)}
          </>
        )}
      </div>

      {/* News Sites Management Section */}
      <section style={{ marginTop: 48 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>News Sites Management</h2>
            <p style={{ margin: "4px 0 0 0", fontSize: 14, opacity: 0.8 }}>
              Configure which sites are active and set default sites (at least 1 required).
            </p>
          </div>
          <button
            onClick={() => setShowAddSite(!showAddSite)}
            style={{
              background: showAddSite ? "#1A1F3A" : "#4C7CF8",
              border: showAddSite ? "1px solid #4C7CF8" : "1px solid #4C7CF8",
              color: showAddSite ? "#4C7CF8" : "white",
              padding: "8px 16px",
              borderRadius: 8,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 500,
              transition: "all 0.2s ease"
            }}
          >
            {showAddSite ? "Cancel" : "Add New Site"}
          </button>
        </div>

        {sitesError && (
          <div role="alert" aria-live="assertive" style={{ 
            background: "#2B1431", 
            border: "1px solid #6B1C3D", 
            padding: 16, 
            borderRadius: 8, 
            marginBottom: 24 
          }}>
            {sitesError}
          </div>
        )}

        {/* Add Site Form */}
        {showAddSite && (
          <div style={{ 
            background: "#0F1527", 
            border: "1px solid #1C2744", 
            borderRadius: 12, 
            padding: 24,
            marginBottom: 24
          }}>
            <h3 style={{ margin: "0 0 16px 0", fontSize: 18, fontWeight: 600 }}>Add New News Site</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 600, color: "#8B92A6" }}>
                  Site Name
                </label>
                <input
                  type="text"
                  value={newSiteName}
                  onChange={(e) => setNewSiteName(e.target.value)}
                  placeholder="e.g., Hacker News"
                  style={{
                    width: "100%",
                    background: "#10162B",
                    border: "1px solid #1C2744",
                    color: "#E6EAF2",
                    padding: "10px 12px",
                    borderRadius: 6,
                    outline: "none",
                    fontSize: 14
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 600, color: "#8B92A6" }}>
                  Site Code
                </label>
                <input
                  type="text"
                  value={newSiteCode}
                  onChange={(e) => setNewSiteCode(e.target.value)}
                  placeholder="e.g., hacker_news"
                  style={{
                    width: "100%",
                    background: "#10162B",
                    border: "1px solid #1C2744",
                    color: "#E6EAF2",
                    padding: "10px 12px",
                    borderRadius: 6,
                    outline: "none",
                    fontSize: 14
                  }}
                />
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 600, color: "#8B92A6" }}>
                Site URL
              </label>
              <input
                type="url"
                value={newSiteUrl}
                onChange={(e) => setNewSiteUrl(e.target.value)}
                placeholder="e.g., https://news.ycombinator.com/"
                style={{
                  width: "100%",
                  background: "#10162B",
                  border: "1px solid #1C2744",
                  color: "#E6EAF2",
                  padding: "10px 12px",
                  borderRadius: 6,
                  outline: "none",
                  fontSize: 14
                }}
              />
            </div>
            <div style={{ display: "flex", gap: 12 }}>
              <button
                onClick={handleAddSite}
                disabled={submittingSite}
                style={{
                  background: submittingSite ? "#2B3658" : "#4C7CF8",
                  border: "none",
                  color: "white",
                  padding: "10px 20px",
                  borderRadius: 6,
                  cursor: submittingSite ? "default" : "pointer",
                  fontSize: 14,
                  fontWeight: 500
                }}
              >
                {submittingSite ? "Adding..." : "Add Site"}
              </button>
              <button
                onClick={() => {
                  setShowAddSite(false);
                  setNewSiteName("");
                  setNewSiteCode("");
                  setNewSiteUrl("");
                  setSitesError(null);
                }}
                style={{
                  background: "transparent",
                  border: "1px solid #1C2744",
                  color: "#8B92A6",
                  padding: "10px 20px",
                  borderRadius: 6,
                  cursor: "pointer",
                  fontSize: 14,
                  fontWeight: 500
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Sites List */}
        {sitesLoading ? (
          <div style={{ 
            display: "flex", 
            justifyContent: "center", 
            alignItems: "center", 
            padding: 64,
            color: "#8B92A6" 
          }}>
            Loading news sites...
          </div>
        ) : sites.length === 0 ? (
          <div style={{ 
            background: "#0F1527", 
            border: "2px dashed #1C2744", 
            borderRadius: 12, 
            padding: 48, 
            textAlign: "center",
            color: "#8B92A6" 
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🌐</div>
            <div style={{ fontSize: 18, marginBottom: 8, fontWeight: 500 }}>
              No news sites configured
            </div>
            <div style={{ fontSize: 14, opacity: 0.8 }}>
              Add your first news site to get started.
            </div>
          </div>
        ) : (
          <div style={{ 
            background: "#0F1527", 
            border: "1px solid #1C2744", 
            borderRadius: 12, 
            overflow: "hidden" 
          }}>
            <div style={{ 
              display: "grid", 
              gridTemplateColumns: "2fr 1fr 2fr 80px 80px 100px 150px",
              gap: 16,
              padding: "16px 20px",
              background: "#1A1F3A",
              borderBottom: "1px solid #1C2744",
              fontSize: 12,
              fontWeight: 600,
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              color: "#8B92A6"
            }}>
              <div>Name</div>
              <div>Code</div>
              <div>URL</div>
              <div>Active</div>
              <div>Default</div>
              <div>Created</div>
              <div>Actions</div>
            </div>
            
            {sites.map((site, idx) => {
              const isEditing = editingSiteId === site.id;
              return (
                <div 
                  key={site.id}
                  style={{ 
                    display: "grid", 
                    gridTemplateColumns: "2fr 1fr 2fr 80px 80px 100px 150px",
                    gap: 16,
                    padding: "16px 20px",
                    borderBottom: idx < sites.length - 1 ? "1px solid #1C2744" : "none",
                    transition: "background 0.2s ease",
                    background: isEditing ? "#151A31" : "transparent"
                  }}
                  onMouseEnter={(e) => {
                    if (!isEditing) {
                      e.currentTarget.style.background = "#151A31";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isEditing) {
                      e.currentTarget.style.background = "transparent";
                    }
                  }}
                >
                  {/* Name Field */}
                  <div style={{ 
                    fontWeight: 500,
                    color: "#E6EAF2",
                    wordBreak: "break-word"
                  }}>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editFormData.name}
                        onChange={(e) => setEditFormData(prev => ({ ...prev, name: e.target.value }))}
                        style={{
                          width: "100%",
                          background: "#10162B",
                          border: "1px solid #1C2744",
                          color: "#E6EAF2",
                          padding: "6px 8px",
                          borderRadius: 4,
                          outline: "none",
                          fontSize: 13,
                          fontWeight: 500
                        }}
                      />
                    ) : (
                      site.name
                    )}
                  </div>
                  
                  {/* Code Field */}
                  <div style={{ 
                    fontSize: 12,
                    color: "#B8BCC8",
                    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
                  }}>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editFormData.code}
                        onChange={(e) => setEditFormData(prev => ({ ...prev, code: e.target.value }))}
                        style={{
                          width: "100%",
                          background: "#10162B",
                          border: "1px solid #1C2744",
                          color: "#B8BCC8",
                          padding: "6px 8px",
                          borderRadius: 4,
                          outline: "none",
                          fontSize: 12,
                          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
                        }}
                      />
                    ) : (
                      site.code
                    )}
                  </div>
                  
                  {/* URL Field */}
                  <div style={{ 
                    fontSize: 12,
                    color: "#4C7CF8",
                    wordBreak: "break-all"
                  }}>
                    {isEditing ? (
                      <input
                        type="url"
                        value={editFormData.url}
                        onChange={(e) => setEditFormData(prev => ({ ...prev, url: e.target.value }))}
                        style={{
                          width: "100%",
                          background: "#10162B",
                          border: "1px solid #1C2744",
                          color: "#4C7CF8",
                          padding: "6px 8px",
                          borderRadius: 4,
                          outline: "none",
                          fontSize: 12
                        }}
                      />
                    ) : (
                      <a href={site.url} target="_blank" rel="noopener noreferrer" style={{ color: "inherit", textDecoration: "none" }}>
                        {site.url}
                      </a>
                    )}
                  </div>
                  
                  {/* Active Toggle */}
                  <div style={{ display: "flex", justifyContent: "center" }}>
                    <button
                      onClick={() => handleToggleSiteActive(site.id, site.is_active)}
                      disabled={isEditing}
                      style={{
                        background: site.is_active ? "#1E3A2A" : "#3A1E1E",
                        color: site.is_active ? "#B8FFCE" : "#FFB8B8",
                        border: `1px solid ${site.is_active ? "#3B5B47" : "#5B3B3B"}`,
                        padding: "4px 8px",
                        borderRadius: 12,
                        fontSize: 10,
                        fontWeight: 600,
                        textTransform: "uppercase",
                        letterSpacing: "0.5px",
                        cursor: isEditing ? "not-allowed" : "pointer",
                        opacity: isEditing ? 0.5 : 1
                      }}
                    >
                      {site.is_active ? "Active" : "Inactive"}
                    </button>
                  </div>
                  
                  {/* Default Toggle */}
                  <div style={{ display: "flex", justifyContent: "center" }}>
                    <button
                      onClick={() => handleToggleSiteDefault(site.id, site.is_default)}
                      disabled={isEditing}
                      style={{
                        background: site.is_default ? "#2A2E1E" : "transparent",
                        color: site.is_default ? "#FFFFC6" : "#8B92A6",
                        border: site.is_default ? "1px solid #5B5F3B" : "1px solid #3A3A3A",
                        padding: "4px 8px",
                        borderRadius: 12,
                        fontSize: 10,
                        fontWeight: 600,
                        textTransform: "uppercase",
                        letterSpacing: "0.5px",
                        cursor: isEditing ? "not-allowed" : "pointer",
                        transition: "all 0.2s ease",
                        opacity: isEditing ? 0.5 : 1
                      }}
                      onMouseEnter={(e) => {
                        if (!site.is_default && !isEditing) {
                          e.currentTarget.style.background = "#2A2E1E";
                          e.currentTarget.style.color = "#FFFFC6";
                          e.currentTarget.style.borderColor = "#5B5F3B";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!site.is_default && !isEditing) {
                          e.currentTarget.style.background = "transparent";
                          e.currentTarget.style.color = "#8B92A6";
                          e.currentTarget.style.borderColor = "#3A3A3A";
                        }
                      }}
                      title={site.is_default ? "Remove from defaults" : "Set as default"}
                    >
                      {site.is_default ? "Default" : "Set Default"}
                    </button>
                  </div>
                  
                  {/* Created Date */}
                  <div style={{ 
                    fontSize: 11,
                    color: "#8B92A6",
                    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
                  }}>
                    {formatDate(site.created_at)}
                  </div>
                  
                  {/* Actions */}
                  <div style={{ display: "flex", gap: 6, justifyContent: "flex-start" }}>
                    {isEditing ? (
                      <>
                        <button
                          onClick={handleSaveEdit}
                          disabled={updatingSite}
                          style={{
                            background: updatingSite ? "#2B3658" : "#4C7CF8",
                            border: "none",
                            color: "white",
                            padding: "4px 8px",
                            borderRadius: 4,
                            fontSize: 10,
                            cursor: updatingSite ? "not-allowed" : "pointer",
                            fontWeight: 500
                          }}
                        >
                          {updatingSite ? "..." : "Save"}
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          disabled={updatingSite}
                          style={{
                            background: "transparent",
                            border: "1px solid #3A3A3A",
                            color: "#8B92A6",
                            padding: "4px 8px",
                            borderRadius: 4,
                            fontSize: 10,
                            cursor: updatingSite ? "not-allowed" : "pointer",
                            fontWeight: 500
                          }}
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => handleEditSite(site)}
                          style={{
                            background: "transparent",
                            border: "1px solid #4C7CF8",
                            color: "#4C7CF8",
                            padding: "4px 8px",
                            borderRadius: 4,
                            fontSize: 10,
                            cursor: "pointer",
                            fontWeight: 500
                          }}
                          title="Edit site"
                        >
                          Edit
                        </button>
                        {!site.is_default && (
                          <button
                            onClick={() => handleDeleteSite(site.id, site.name)}
                            style={{
                              background: "transparent",
                              border: "1px solid #5B3B3B",
                              color: "#FFB8B8",
                              padding: "4px 8px",
                              borderRadius: 4,
                              fontSize: 10,
                              cursor: "pointer",
                              fontWeight: 500
                            }}
                            title="Delete site"
                          >
                            Delete
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div style={{ 
          marginTop: 24, 
          padding: 16, 
          background: "#0F1527", 
          border: "1px solid #1C2744", 
          borderRadius: 8,
          fontSize: 12,
          color: "#8B92A6"
        }}>
          <strong style={{ color: "#E6EAF2" }}>Total Sites:</strong> {sites.length}
          {sites.length > 0 && (
            <>
              {" • "}
              <strong style={{ color: "#E6EAF2" }}>Active:</strong> {sites.filter(s => s.is_active).length}
              {" • "}
              <strong style={{ color: "#E6EAF2" }}>Default:</strong> {sites.filter(s => s.is_default).length}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
