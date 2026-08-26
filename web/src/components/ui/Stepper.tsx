/* eslint-disable no-restricted-syntax */
import React, { useState, Children, useRef, useLayoutEffect, ReactNode, isValidElement } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import './Stepper.css';

export interface StepProps {
  children: ReactNode;
  title?: string;
  className?: string;
}

export function Step({ children, className }: StepProps) {
  return <div className={cn("step-default", className)}>{children}</div>;
}

export interface StepperProps {
  children: ReactNode;
  initialStep?: number;
  onStepChange?: (step: number) => void;
  onFinalStepCompleted?: () => void;
  stepCircleContainerClassName?: string;
  stepContainerClassName?: string;
  contentClassName?: string;
  footerClassName?: string;
  backButtonProps?: React.ButtonHTMLAttributes<HTMLButtonElement>;
  nextButtonProps?: React.ButtonHTMLAttributes<HTMLButtonElement>;
  backButtonText?: string;
  nextButtonText?: string;
  disableStepIndicators?: boolean;
  activeStep?: number;
  renderStepIndicator?: (props: {
    step: number;
    currentStep: number;
    onStepClick: (step: number) => void;
    title?: string;
  }) => ReactNode;
  className?: string;
}

export function Stepper({
  children,
  initialStep = 1,
  onStepChange = () => {},
  onFinalStepCompleted = () => {},
  stepCircleContainerClassName = '',
  stepContainerClassName = '',
  contentClassName = '',
  footerClassName = '',
  backButtonProps = {},
  nextButtonProps = {},
  backButtonText = 'Previous',
  nextButtonText = 'Next',
  disableStepIndicators = false,
  activeStep: controlledStep,
  renderStepIndicator,
  className = '',
  ...rest
}: StepperProps) {
  const [internalStep, setInternalStep] = useState(initialStep);
  const [direction, setDirection] = useState(0);

  const currentStep = controlledStep !== undefined ? controlledStep : internalStep;
  const stepsArray = Children.toArray(children);
  const totalSteps = stepsArray.length;
  const isCompleted = currentStep > totalSteps;
  const isLastStep = currentStep === totalSteps;

  const updateStep = (newStep: number) => {
    if (controlledStep === undefined) {
      setInternalStep(newStep);
    }
    if (newStep > totalSteps) {
      onFinalStepCompleted();
    } else {
      onStepChange(newStep);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setDirection(-1);
      updateStep(currentStep - 1);
    }
  };

  const handleNext = () => {
    if (!isLastStep) {
      setDirection(1);
      updateStep(currentStep + 1);
    }
  };

  const handleComplete = () => {
    setDirection(1);
    updateStep(1); // loop back to first step when complete
  };

  return (
    <div className={cn("stepper-outer-container", className)} {...rest}>
      <div className={`stepper-circle-container ${stepCircleContainerClassName}`}>
        <div className={`stepper-indicator-row ${stepContainerClassName}`}>
          {stepsArray.map((child, index) => {
            const stepNumber = index + 1;
            const isNotLastStep = index < totalSteps - 1;
            const stepTitle = isValidElement<StepProps>(child) ? child.props.title : undefined;

            return (
              <React.Fragment key={stepNumber}>
                {renderStepIndicator ? (
                  renderStepIndicator({
                    step: stepNumber,
                    currentStep,
                    onStepClick: (clicked) => {
                      setDirection(clicked > currentStep ? 1 : -1);
                      updateStep(clicked);
                    },
                    title: stepTitle,
                  })
                ) : (
                  <StepIndicator
                    step={stepNumber}
                    title={stepTitle}
                    disableStepIndicators={disableStepIndicators}
                    currentStep={currentStep}
                    onClickStep={(clicked) => {
                      setDirection(clicked > currentStep ? 1 : -1);
                      updateStep(clicked);
                    }}
                  />
                )}
                {isNotLastStep && <StepConnector isComplete={currentStep > stepNumber} />}
              </React.Fragment>
            );
          })}
        </div>

        <StepContentWrapper
          isCompleted={isCompleted}
          currentStep={currentStep}
          direction={direction}
          className={`stepper-content-default ${contentClassName}`}
        >
          {stepsArray[currentStep - 1]}
        </StepContentWrapper>

        {!isCompleted && (
          <div className={`stepper-footer-container ${footerClassName}`}>
            <div className={`stepper-footer-nav ${currentStep !== 1 ? 'spread' : 'end'}`}>
              {currentStep !== 1 && (
                <button
                  onClick={handleBack}
                  className={`stepper-back-btn ${currentStep === 1 ? 'inactive' : ''}`}
                  {...backButtonProps}
                >
                  {backButtonText}
                </button>
              )}
              <button
                onClick={isLastStep ? handleComplete : handleNext}
                className="stepper-next-btn"
                {...nextButtonProps}
              >
                {isLastStep ? 'Restart' : nextButtonText}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StepContentWrapper({
  isCompleted,
  currentStep,
  direction,
  children,
  className,
}: {
  isCompleted: boolean;
  currentStep: number;
  direction: number;
  children: ReactNode;
  className: string;
}) {
  const [parentHeight, setParentHeight] = useState<number | 'auto'>('auto');

  return (
    <motion.div
      className={className}
      style={{ position: 'relative', overflow: 'hidden' }}
      animate={{ height: isCompleted ? 0 : parentHeight }}
      transition={{ type: 'spring', duration: 0.4 }}
    >
      <AnimatePresence initial={false} mode="sync" custom={direction}>
        {!isCompleted && (
          <SlideTransition key={currentStep} direction={direction} onHeightReady={(h) => setParentHeight(h)}>
            {children}
          </SlideTransition>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function SlideTransition({
  children,
  direction,
  onHeightReady,
}: {
  children: ReactNode;
  direction: number;
  onHeightReady: (height: number) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (containerRef.current) onHeightReady(containerRef.current.offsetHeight);
  }, [children, onHeightReady]);

  return (
    <motion.div
      ref={containerRef}
      custom={direction}
      variants={stepVariants}
      initial="enter"
      animate="center"
      exit="exit"
      transition={{ duration: 0.4 }}
      style={{ position: 'relative', width: '100%' }}
    >
      {children}
    </motion.div>
  );
}

const stepVariants = {
  enter: (dir: number) => ({
    x: dir >= 0 ? '60%' : '-60%',
    opacity: 0,
  }),
  center: {
    x: '0%',
    opacity: 1,
  },
  exit: (dir: number) => ({
    x: dir >= 0 ? '-60%' : '60%',
    opacity: 0,
  }),
};

function StepIndicator({
  step,
  title,
  currentStep,
  onClickStep,
  disableStepIndicators,
}: {
  step: number;
  title?: string;
  currentStep: number;
  onClickStep: (step: number) => void;
  disableStepIndicators: boolean;
}) {
  const status = currentStep === step ? 'active' : currentStep < step ? 'inactive' : 'complete';

  const handleClick = () => {
    if (step !== currentStep && !disableStepIndicators) onClickStep(step);
  };

  return (
    <motion.div
      onClick={handleClick}
      className="stepper-indicator-wrapper"
      style={disableStepIndicators ? { pointerEvents: 'none', opacity: 0.5 } : {}}
      animate={status}
      initial={false}
    >
      <motion.div
        variants={{
          inactive: { scale: 1, backgroundColor: '#f0f2f4', color: '#666666' },
          active: { scale: 1, backgroundColor: '#006df8', color: '#ffffff' },
          complete: { scale: 1, backgroundColor: '#006df8', color: '#ffffff' },
        }}
        transition={{ duration: 0.3 }}
        className="stepper-indicator-inner"
      >
        {status === 'complete' ? (
          <CheckIcon className="stepper-check-icon" />
        ) : status === 'active' ? (
          <div className="stepper-active-dot" />
        ) : (
          <span className="stepper-step-number">{step}</span>
        )}
      </motion.div>
      {title && <span className={`stepper-label stepper-label--${status}`}>{title}</span>}
    </motion.div>
  );
}

function StepConnector({ isComplete }: { isComplete: boolean }) {
  const lineVariants = {
    incomplete: { width: 0, backgroundColor: 'transparent' },
    complete: { width: '100%', backgroundColor: '#006df8' },
  };

  return (
    <div className="stepper-connector">
      <motion.div
        className="stepper-connector-inner"
        variants={lineVariants}
        initial={false}
        animate={isComplete ? 'complete' : 'incomplete'}
        transition={{ duration: 0.4 }}
      />
    </div>
  );
}

function CheckIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg {...props} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
      <motion.path
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ delay: 0.1, type: 'tween', ease: 'easeOut', duration: 0.3 }}
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}

export default Stepper;
