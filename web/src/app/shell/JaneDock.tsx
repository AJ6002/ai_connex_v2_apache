import { useState } from 'react';
import { useJaneSession, useExecuteJaneAction, useResolveJaneClarification } from '@/entities/jane/hooks';
import { AsyncState } from '@/components/AsyncState';
import './JaneDock.css';

type DockTab = 'intent' | 'jobs' | 'actions';

/**
 * Jane assistant dock — faithful to STITCH-Design jane_intent_clarification_flow /
 * jane_analysis_intent_clarification(_refined). Renders the live session transcript,
 * an interactive clarification question, and — once resolved — a proposed action
 * card the user must explicitly execute (agents propose, user/deterministic
 * services execute).
 */
export function JaneDock() {
  const [tab, setTab] = useState<DockTab>('intent');
  const { data: session, isLoading, isError, error } = useJaneSession();
  const resolveClarification = useResolveJaneClarification();
  const executeAction = useExecuteJaneAction();

  return (
    <aside className="jane" aria-label="Jane assistant">
      <header className="jane__header">
        <div className="jane__identity">
          <div className="jane__title-row">
            <span className={`jane__dot${session?.status === 'ONLINE' ? '' : ' jane__dot--idle'}`} aria-hidden="true" />
            <span className="jane__title">JANE_AI</span>
          </div>
          <span className="jane__status label-mono">
            {session?.clarification && !session.clarification.resolvedOption ? 'INTENT_RESOLUTION' : 'SYSTEM_READY'}
          </span>
        </div>
        <button type="button" className="jane__expand label-mono">
          EXPAND_VIEW
        </button>
      </header>

      <div className="jane__tabs" role="tablist">
        {(['intent', 'jobs', 'actions'] as const).map((t) => (
          <button
            key={t}
            type="button"
            role="tab"
            aria-selected={tab === t}
            className={`jane__tab label-mono${tab === t ? ' jane__tab--active' : ''}`}
            onClick={() => setTab(t)}
          >
            <span className="material-symbols-outlined">
              {t === 'intent' ? 'psychology' : t === 'jobs' ? 'work' : 'bolt'}
            </span>
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      <AsyncState isLoading={isLoading} isError={isError} error={error}>
        {session && (
          <div className="jane__body">
            {tab === 'intent' ? (
              <>
                {session.turns
                  .filter((t) => t.role === 'user')
                  .slice(-1)
                  .map((t) => (
                    <div key={t.turnId} className="jane__intent-box">
                      <p>{t.text}</p>
                    </div>
                  ))}

                {session.clarification && (
                  <div className="jane__clarify">
                    <span className="jane__clarify-head label-mono">
                      <span className="material-symbols-outlined">help</span> CLARIFICATION_REQUIRED
                    </span>
                    <p>{session.clarification.question}</p>
                    {!session.clarification.resolvedOption ? (
                      <div className="jane__clarify-opts">
                        {session.clarification.options.map((opt) => (
                          <button
                            key={opt}
                            type="button"
                            className="jane__opt"
                            disabled={resolveClarification.isPending}
                            onClick={() => resolveClarification.mutate(opt)}
                          >
                            <span className="material-symbols-outlined">
                              {opt.toLowerCase() === 'staging' ? 'science' : 'rocket_launch'}
                            </span>
                            {opt}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <span className="jane__resolved label-mono">&gt; Select: {session.clarification.resolvedOption}</span>
                    )}
                  </div>
                )}

                {session.proposedAction && (
                  <div className="jane__action">
                    <span className="jane__action-head label-mono">
                      <span className="material-symbols-outlined">build</span> ACTION_PROPOSED
                      <span className="jane__action-pending">
                        {session.proposedAction.executed ? 'EXECUTED' : 'PENDING_INPUT'}
                      </span>
                    </span>
                    <div className="jane__action-card">
                      <div className="jane__action-card-head">
                        <span>{session.proposedAction.title}</span>
                        <span className="material-symbols-outlined">query_stats</span>
                      </div>
                      <p className="jane__action-target">{session.proposedAction.targetLabel}</p>
                      <dl className="jane__action-params">
                        {session.proposedAction.params.map((p) => (
                          <div key={p.label}>
                            <dt className="label-mono">{p.label}</dt>
                            <dd>{p.value}</dd>
                          </div>
                        ))}
                      </dl>
                      <button
                        type="button"
                        className="jane__execute label-mono"
                        disabled={session.proposedAction.executed || executeAction.isPending}
                        onClick={() => executeAction.mutate()}
                      >
                        <span className="material-symbols-outlined">play_arrow</span>
                        {session.proposedAction.executed ? 'JOB_SUBMITTED' : session.proposedAction.executeLabel}
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="jane__msg">
                <p>No {tab} to display in this session.</p>
              </div>
            )}
          </div>
        )}
      </AsyncState>

      <form className="jane__input" onSubmit={(e) => e.preventDefault()}>
        <span className="jane__prompt">_</span>
        <input
          className="jane__field label-mono"
          placeholder="READY_FOR_INPUT..."
          aria-label="Message Jane"
        />
        <button type="submit" className="jane__send" aria-label="Send">
          <span className="material-symbols-outlined">send</span>
        </button>
      </form>
    </aside>
  );
}
