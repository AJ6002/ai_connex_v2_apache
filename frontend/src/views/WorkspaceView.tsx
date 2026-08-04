import React, { useState, useEffect } from 'react';

interface WorkspaceItem {
  name: string;
  path: string;
  size_bytes: number;
  is_dir: boolean;
}

export const WorkspaceView: React.FC = () => {
  const [items, setItems] = useState<WorkspaceItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchWorkspaceFiles = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/workspace/files');
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || []);
      }
    } catch (err) {
      console.error("Error fetching workspace files:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaceFiles();
  }, []);

  const formatSize = (bytes: number) => {
    if (bytes === 0) return 'Directory';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (name: string, isDir: boolean) => {
    if (isDir) return { icon: 'folder', color: '#F59E0B' };
    const ext = name.split('.').pop()?.toLowerCase();
    if (ext === 'csv') return { icon: 'table_view', color: '#10B981' };
    if (ext === 'pkl') return { icon: 'model_training', color: '#3B82F6' };
    if (ext === 'zip') return { icon: 'folder_zip', color: '#EF4444' };
    if (ext === 'txt') return { icon: 'description', color: '#F97316' };
    return { icon: 'draft', color: '#6B7280' };
  };

  // Group items by directory or flat list
  const filteredItems = items.filter(item => 
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.path.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 text-primary animate-fadeIn">
      {/* Title Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-tas-red/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 text-muted text-xs font-mono uppercase tracking-widest mb-1">
              <span className="text-tas-red font-extrabold">TENANT DOCK</span>
              <span>•</span>
              <span className="text-cb font-bold">Workspace Repository</span>
            </div>
            <h1 className="font-headline text-2xl sm:text-3xl font-extrabold text-primary tracking-tight">
              My Workspace
            </h1>
          </div>
          <button 
            onClick={fetchWorkspaceFiles}
            className="px-3.5 py-1.5 border border-ui rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5 hover:bg-slate-50 dark:hover:bg-slate-850 text-primary"
          >
            <span className="material-symbols-outlined text-xs">sync</span>
            <span>Refresh Workspace</span>
          </button>
        </div>
      </div>

      {/* Explorer Controls */}
      <div className="glass-panel p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-sm text-secondary">search</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files, folders, extensions..."
            className="w-full rounded-xl pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 dark:bg-slate-850 dark:border-slate-800 dark:text-white"
          />
        </div>
        <span className="text-xs font-mono text-secondary">
          Displaying {filteredItems.length} items in tenant repository folder
        </span>
      </div>

      {isLoading ? (
        <div className="glass-panel p-16 flex flex-col items-center justify-center space-y-4">
          <div className="w-10 h-10 border-4 border-tas-red border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs font-mono text-slate-500">Retrieving workspace structure...</span>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="glass-panel p-16 flex flex-col items-center justify-center text-center space-y-3">
          <span className="material-symbols-outlined text-4xl text-slate-400">folder_open</span>
          <h3 className="font-headline font-bold text-sm text-primary">Workspace is Empty</h3>
          <p className="text-xs text-secondary max-w-xs">
            Compile a dataset or upload files to populate the workspace directory.
          </p>
        </div>
      ) : (
        <div className="glass-panel overflow-hidden border border-ui rounded-3xl">
          {/* File list table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-ui bg-slate-50 dark:bg-slate-900/40 text-[10px] font-mono font-bold uppercase text-secondary">
                  <th className="p-4">Name / Path</th>
                  <th className="p-4">File Type</th>
                  <th className="p-4">Size</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ui">
                {filteredItems.map((item, idx) => {
                  const meta = getFileIcon(item.name, item.is_dir);
                  return (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/10 transition-colors">
                      <td className="p-4 flex items-center gap-3">
                        <span className="material-symbols-outlined text-lg" style={{ color: meta.color }}>
                          {meta.icon}
                        </span>
                        <div>
                          <p className="font-mono text-xs font-bold text-primary truncate max-w-md">{item.name}</p>
                          <p className="text-[10px] text-secondary font-mono truncate max-w-md">{item.path}</p>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-slate-100 dark:bg-slate-900 text-secondary border border-ui">
                          {item.is_dir ? 'Folder' : item.name.split('.').pop() || 'Unknown'}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-xs text-secondary">
                        {formatSize(item.size_bytes)}
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => {
                            alert(`File selected: ${item.path}\nUse this path dynamically in Node control views!`);
                          }}
                          className="px-2.5 py-1 text-[10px] font-mono font-bold rounded-lg border border-ui text-primary hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
                        >
                          Select Path
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
