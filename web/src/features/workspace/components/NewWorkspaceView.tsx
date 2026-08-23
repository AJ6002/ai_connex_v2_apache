import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui';
import { useCreateWorkspace } from '@/entities/workspace/hooks';
import './NewWorkspaceView.css';

export function NewWorkspaceView() {
  const navigate = useNavigate();
  const create = useCreateWorkspace();

  const [name, setName] = useState('');
  const [region, setRegion] = useState('us-east-1');
  const [privacyMode, setPrivacyMode] = useState<'PRIVATE_CLOUD' | 'SHARED_CLOUD'>('PRIVATE_CLOUD');

  const handleCreate = () => {
    create.mutate({ name, primaryRegion: region, privacyMode }, { onSuccess: () => navigate('/') });
  };

  return (
    <div className="nws">
      <section className="nws__panel">
        <h1 className="nws__title">New Workspace</h1>
        <p className="nws__sub">Provision an isolated workspace with its own compute, storage, and policies.</p>

        <label className="nws__field">
          <span className="label-mono">WORKSPACE NAME</span>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Project Beta - Staging" />
        </label>

        <label className="nws__field">
          <span className="label-mono">PRIMARY REGION</span>
          <div className="nws__select">
            <select value={region} onChange={(e) => setRegion(e.target.value)}>
              <option value="us-east-1">us-east-1 (N. Virginia)</option>
              <option value="eu-west-1">eu-west-1 (Ireland)</option>
              <option value="ap-south-1">ap-south-1 (Mumbai)</option>
            </select>
            <span className="material-symbols-outlined">expand_more</span>
          </div>
        </label>

        <div className="nws__field">
          <span className="label-mono">PRIVACY MODE</span>
          <div className="nws__segmented">
            {(['PRIVATE_CLOUD', 'SHARED_CLOUD'] as const).map((m) => (
              <button
                key={m}
                type="button"
                className={`nws__seg label-mono${privacyMode === m ? ' nws__seg--active' : ''}`}
                onClick={() => setPrivacyMode(m)}
              >
                {m === 'PRIVATE_CLOUD' ? 'PRIVATE CLOUD' : 'SHARED CLOUD'}
              </button>
            ))}
          </div>
        </div>

        <div className="nws__actions">
          <Button variant="secondary" onClick={() => navigate('/')}>Cancel</Button>
          <Button
            variant="primary"
            disabled={!name.trim()}
            loading={create.isPending}
            onClick={handleCreate}
            rightIcon={<span className="material-symbols-outlined">north_east</span>}
          >
            Create Workspace
          </Button>
        </div>
      </section>
    </div>
  );
}
