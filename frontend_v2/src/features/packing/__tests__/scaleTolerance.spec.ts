import { describe, it, expect } from 'vitest';
import {
  evaluateScaleTolerance,
  generateErro01SNPreview,
} from '../utils/scaleTolerance';

describe('evaluateScaleTolerance', () => {
  const defaultProduct = {
    min_weight: 12.300,
    target_weight: 12.500,
    max_weight: 12.700,
  };

  it('returns DISCONNECTED when scale is disconnected', () => {
    const res = evaluateScaleTolerance({
      isConnected: false,
      currentWeight: 12.500,
      isStable: true,
      product: defaultProduct,
    });
    expect(res.status).toBe('DISCONNECTED');
    expect(res.canPrint).toBe(false);
  });

  it('returns UNSTABLE when scale weight fluctuates', () => {
    const res = evaluateScaleTolerance({
      isConnected: true,
      currentWeight: 12.500,
      isStable: false,
      product: defaultProduct,
    });
    expect(res.status).toBe('UNSTABLE');
    expect(res.canPrint).toBe(false);
  });

  it('returns UNDERWEIGHT when weight is below min tolerance', () => {
    const res = evaluateScaleTolerance({
      isConnected: true,
      currentWeight: 12.100,
      isStable: true,
      product: defaultProduct,
    });
    expect(res.status).toBe('UNDERWEIGHT');
    expect(res.canPrint).toBe(false);
  });

  it('returns OVERWEIGHT when weight is above max tolerance', () => {
    const res = evaluateScaleTolerance({
      isConnected: true,
      currentWeight: 12.850,
      isStable: true,
      product: defaultProduct,
    });
    expect(res.status).toBe('OVERWEIGHT');
    expect(res.canPrint).toBe(false);
  });

  it('returns READY when weight is within range and stable', () => {
    const res = evaluateScaleTolerance({
      isConnected: true,
      currentWeight: 12.500,
      isStable: true,
      product: defaultProduct,
    });
    expect(res.status).toBe('READY');
    expect(res.canPrint).toBe(true);
  });

  it('returns READY at boundary minimum weight', () => {
    const res = evaluateScaleTolerance({
      isConnected: true,
      currentWeight: 12.300,
      isStable: true,
      product: defaultProduct,
    });
    expect(res.status).toBe('READY');
    expect(res.canPrint).toBe(true);
  });

  it('returns READY at boundary maximum weight', () => {
    const res = evaluateScaleTolerance({
      isConnected: true,
      currentWeight: 12.700,
      isStable: true,
      product: defaultProduct,
    });
    expect(res.status).toBe('READY');
    expect(res.canPrint).toBe(true);
  });
});

describe('generateErro01SNPreview', () => {
  it('formats prefix, yymm, and 6-digit sequence', () => {
    expect(generateErro01SNPreview('VHK0010237', '2608', 81)).toBe('VHK00102372608000081');
    expect(generateErro01SNPreview('VHK0010237', '2608', 1)).toBe('VHK00102372608000001');
    expect(generateErro01SNPreview('VHK0010237', '2608', '123456')).toBe('VHK00102372608123456');
  });
});
