import * as React from 'react';
import {useEffect, useState} from 'react';
import axios from 'axios';
import randomSlug from '../slug';

export function Shortener() {
    const [slug, setSlug] = useState('');
    const [url, setUrl] = useState('https://example.com');

    useEffect(() => {
        randomSlug(6).then(slug => setSlug(slug));
    }, []);

    function shorten() {
        axios.post('/api/shorten/', {slug, url}).catch(err => {
            if (err.status === 409) {
                alert('This short URL is occupied. Please try another one.');
                return;
            }
            alert('An unexpected error has occurred. Please try again later.');
            console.error(err);
        });
    }

    return <div>
        short.en/
        <input className="slug" value={slug} onChange={e => setSlug(e.target.value)}
               title="Shortened URL part"/>
        &nbsp;=&nbsp;
        <input className="url" value={url} onChange={e => setUrl(e.target.value)}
               title="URL to shorten"/>
        <button onClick={shorten}>Shorten</button>
    </div>;
}
