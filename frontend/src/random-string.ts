export default function randomString(length: number): string {
    if (length < 1) {
        throw Error(`invalid random string length: ${length}`);
    }
    return Math.random().toString(36).substr(2, length);
}
