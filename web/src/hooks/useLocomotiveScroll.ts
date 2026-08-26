import { useEffect } from 'react';
import LocomotiveScroll from 'locomotive-scroll';
import 'locomotive-scroll/dist/locomotive-scroll.css';

export function useLocomotiveScroll() {
  useEffect(() => {
    let scrollInstance: LocomotiveScroll | null = null;

    try {
      scrollInstance = new LocomotiveScroll({
        lenisOptions: {
          wrapper: window,
          content: document.documentElement,
          lerp: 0.1,
          duration: 1.2,
          orientation: 'vertical',
          gestureOrientation: 'vertical',
          smoothWheel: true,
          wheelMultiplier: 1,
          touchMultiplier: 2,
        },
      });
    } catch (err) {
      console.warn('LocomotiveScroll init warning:', err);
    }

    return () => {
      scrollInstance?.destroy();
    };
  }, []);
}

export default useLocomotiveScroll;
