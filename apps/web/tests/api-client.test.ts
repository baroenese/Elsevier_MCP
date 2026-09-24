import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { fmt } from '../lib/api-client.ts';

describe('api-client utilities', () => {
  describe('fmt()', () => {
    it('formats positive numbers with thousands separators', () => {
      assert.equal(fmt(1234), '1,234');
      assert.equal(fmt(1000000), '1,000,000');
    });

    it('formats numeric strings correctly', () => {
      assert.equal(fmt('5678'), '5,678');
      assert.equal(fmt('42'), '42');
    });

    it('handles zero gracefully', () => {
      assert.equal(fmt(0), '0');
      assert.equal(fmt('0'), '0');
    });

    it('handles null and undefined gracefully by returning 0', () => {
      assert.equal(fmt(null), '0');
      assert.equal(fmt(undefined), '0');
    });
  });

  describe('ISSN detection logic', () => {
    function isIssn(query: string): boolean {
      return query.replace(/-/g, '').length === 8 && !query.includes(' ');
    }

    it('identifies standard hyphenated 8-digit ISSN', () => {
      assert.equal(isIssn('0098-5589'), true);
      assert.equal(isIssn('2522-5839'), true);
    });

    it('identifies unhyphenated 8-character ISSN', () => {
      assert.equal(isIssn('00985589'), true);
    });

    it('rejects general text query containing spaces or non-8 length', () => {
      assert.equal(isIssn('Nature Machine Intelligence'), false);
      assert.equal(isIssn('IEEE TSE'), false);
      assert.equal(isIssn('12345'), false);
      assert.equal(isIssn('1234-56789'), false);
    });
  });
});
