import React, { useRef, useEffect } from 'react';
import './MagneticWrapper.css';

export const MagneticWrapper: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const move = (e: MouseEvent) => {
      const { left, top, width, height } = el.getBoundingClientRect();
      const x = (e.clientX - (left + width / 2)) * 0.4;
      const y = (e.clientY - (top + height / 2)) * 0.4;
      el.style.transform = `translate(${x}px, ${y}px)`;
    };
    const reset = () => { el.style.transform = `translate(0px, 0px)`; };
    el.addEventListener('mousemove', move);
    el.addEventListener('mouseleave', reset);
    return () => { el.removeEventListener('mousemove', move); el.removeEventListener('mouseleave', reset); };
  }, []);
  return <div ref={ref} className="magnetic-container">{children}</div>;
};
