import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui';
import { useCreateDeployment } from '@/entities/deployment/hooks';
import './DeploymentConfigView.css';

export function DeploymentConfigView() {
  const navigate = useNavigate();
  const create = useCreateDeployment();

  const [modelRef, setModelRef] = useState('CHURN-V3 v1.2.4');
  const [environment, setEnvironment] = useState<'PRODUCTION' | 'STAGING'>('PRODUCTION');
  const [replicas, setReplicas] = useState(3);
  const [region, setRegion] = useState('us-east-1');
  const [instance, setInstance] = useState('ml.m5.xlarge');

  const handleDeploy = () => {
    create.mutate(
      { name: `${modelRef}-serving`, modelRef, environment, replicas },
      { onSuccess: () => navigate('/deployments') },
    );
  };

  return (
    <div className="depc">
      <header className="depc__header">
        <h1 className="depc__title">New Deployment</h1>
        <p className="depc__sub">Configure serving infrastructure for a promoted model artifact.</p>
      </header>

      <section className="depc__panel">
        <span className="label-mono depc__panel-title">DEPLOYMENT CONFIGURATION</span>

        <label className="depc__field">
          <span className="label-mono">MODEL ARTIFACT</span>
          <div className="depc__select">
            <select value={modelRef} onChange={(e) => setModelRef(e.target.value)}>
              <option>CHURN-V3 v1.2.4</option>
              <option>NLP-SENTIMENT v2.0.1</option>
            </select>
            <span className="material-symbols-outlined">expand_more</span>
          </div>
        </label>

        <div className="depc__field">
          <span className="label-mono">TARGET ENVIRONMENT</span>
          <div className="depc__segmented">
            {(['PRODUCTION', 'STAGING'] as const).map((e) => (
              <button
                key={e}
                type="button"
                className={`depc__seg label-mono${environment === e ? ' depc__seg--active' : ''}`}
                onClick={() => setEnvironment(e)}
              >
                {e}
              </button>
            ))}
          </div>
        </div>

        <div className="depc__field-row">
          <label className="depc__field">
            <span className="label-mono">COMPUTE REGION</span>
            <div className="depc__select">
              <select value={region} onChange={(e) => setRegion(e.target.value)}>
                <option>us-east-1</option>
                <option>eu-west-1</option>
                <option>ap-south-1</option>
              </select>
              <span className="material-symbols-outlined">expand_more</span>
            </div>
          </label>
          <label className="depc__field">
            <span className="label-mono">INSTANCE TYPE</span>
            <div className="depc__select">
              <select value={instance} onChange={(e) => setInstance(e.target.value)}>
                <option>ml.m5.xlarge</option>
                <option>ml.c5.large</option>
                <option>ml.g4dn.xlarge</option>
              </select>
              <span className="material-symbols-outlined">expand_more</span>
            </div>
          </label>
          <label className="depc__field">
            <span className="label-mono">REPLICAS</span>
            <div className="depc__input">
              <input type="number" min={1} value={replicas} onChange={(e) => setReplicas(Number(e.target.value))} />
            </div>
          </label>
        </div>

        <div className="depc__actions">
          <Button variant="secondary" onClick={() => navigate('/deployments')}>Cancel</Button>
          <Button
            variant="primary"
            onClick={handleDeploy}
            loading={create.isPending}
            rightIcon={<span className="material-symbols-outlined">rocket_launch</span>}
          >
            Deploy
          </Button>
        </div>
      </section>
    </div>
  );
}
