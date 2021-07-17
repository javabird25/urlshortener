import axios from 'axios';
import randomString from './random-string';

export default async function randomSlug(length: number): Promise<string> {
    try {
        return (await axios.get(`/api/slug/?length=${length}`)).data;
    } catch (e) {
        console.error(e);
        return randomString(length);
    }
}
