import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import {
  Button,
  Card, CardHeader, CardBody,
  Input,
  StatusBadge,
  Progress,
  SkeletonText,
  EmptyState,
  ErrorState,
  Tabs, TabList, TabTrigger, TabPanel,
  DataTable,
} from '../index';
import type { DataTableColumn } from '../index';

describe('UI Primitives — Design System Foundation', () => {
  describe('<Button />', () => {
    it('renders with default primary variant and handles click', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Submit</Button>);
      const btn = screen.getByRole('button', { name: /submit/i });
      expect(btn).toHaveClass('btn', 'btn-primary', 'btn-md');
      fireEvent.click(btn);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('renders as anchor when href is provided', () => {
      render(<Button href="/intake" variant="secondary">Go to Intake</Button>);
      const link = screen.getByRole('link', { name: /go to intake/i });
      expect(link).toHaveAttribute('href', '/intake');
      expect(link).toHaveClass('btn', 'btn-secondary');
    });

    it('disables button when disabled or loading', () => {
      render(<Button disabled loading>Disabled</Button>);
      const btn = screen.getByRole('button');
      expect(btn).toBeDisabled();
    });
  });

  describe('<Card />', () => {
    it('renders with elevation and accent classes', () => {
      const { container } = render(
        <Card elevation="high" accent="lime">
          <CardHeader title="TEST_CARD" />
          <CardBody>Card content</CardBody>
        </Card>,
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('card', 'card--high', 'card--accent-lime');
      expect(screen.getByText('TEST_CARD')).toBeInTheDocument();
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });
  });

  describe('<Input />', () => {
    it('renders label, input, and error message', () => {
      render(<Input label="USERNAME" error="Field required" placeholder="Enter name" />);
      expect(screen.getByText('USERNAME')).toBeInTheDocument();
      const input = screen.getByPlaceholderText('Enter name');
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(screen.getByText('Field required')).toBeInTheDocument();
    });
  });

  describe('<StatusBadge />', () => {
    it('renders mapped label and status variant', () => {
      render(<StatusBadge status="RUNNING" dot />);
      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('status-badge', 'status-badge--running');
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  describe('<Progress />', () => {
    it('renders progress track with percentage label', () => {
      render(<Progress value={75} label="TRAINING" showValue variant="lime" />);
      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toHaveAttribute('aria-valuenow', '75');
      expect(screen.getByText('75%')).toBeInTheDocument();
    });
  });

  describe('<Tabs />', () => {
    it('switches active panel when tab trigger is clicked', () => {
      render(
        <Tabs defaultTab="tab1">
          <TabList>
            <TabTrigger id="tab1">Tab One</TabTrigger>
            <TabTrigger id="tab2">Tab Two</TabTrigger>
          </TabList>
          <TabPanel id="tab1">Panel One Content</TabPanel>
          <TabPanel id="tab2">Panel Two Content</TabPanel>
        </Tabs>,
      );

      expect(screen.getByText('Panel One Content')).toBeInTheDocument();
      expect(screen.queryByText('Panel Two Content')).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole('tab', { name: /tab two/i }));

      expect(screen.queryByText('Panel One Content')).not.toBeInTheDocument();
      expect(screen.getByText('Panel Two Content')).toBeInTheDocument();
    });
  });

  describe('<DataTable />', () => {
    it('renders headers, rows, and handles empty data state', () => {
      type Row = { id: string; name: string };
      const columns: DataTableColumn<Row>[] = [
        { key: 'name', header: 'NAME', cell: (r) => r.name },
      ];
      const { rerender } = render(
        <DataTable columns={columns} data={[{ id: '1', name: 'Alice' }]} rowKey={(r) => r.id} />,
      );
      expect(screen.getByText('Alice')).toBeInTheDocument();

      rerender(
        <DataTable columns={columns} data={[]} rowKey={(r) => r.id} emptyMessage="EMPTY_TABLE" />,
      );
      expect(screen.getByText('EMPTY_TABLE')).toBeInTheDocument();
    });
  });

  describe('<EmptyState /> & <ErrorState />', () => {
    it('renders EmptyState title and description', () => {
      render(<EmptyState title="NO_ITEMS" description="Nothing to display" />);
      expect(screen.getByText('NO_ITEMS')).toBeInTheDocument();
      expect(screen.getByText('Nothing to display')).toBeInTheDocument();
    });

    it('renders ErrorState with retry button', () => {
      const handleRetry = vi.fn();
      render(<ErrorState title="FAILED" message="Connection error" retry={handleRetry} />);
      expect(screen.getByText('FAILED')).toBeInTheDocument();
      const retryBtn = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryBtn);
      expect(handleRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('<Skeleton />', () => {
    it('renders skeleton line placeholder', () => {
      render(<SkeletonText lines={2} />);
      const skeletons = document.querySelectorAll('.skeleton');
      expect(skeletons.length).toBe(2);
    });
  });
});
