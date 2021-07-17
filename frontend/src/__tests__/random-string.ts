import randomString from '../random-string';
import each from 'jest-each';

each([6, 1]).it('can return strings of length %d', length => {
    const str = randomString(length);

    expect(str).toHaveLength(length);
});

each([-1, 0]).it('throws on invalid length of %d', length => {
    expect(() => randomString(length)).toThrow();
});
