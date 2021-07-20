import React, {useEffect, useState} from 'react';
import axios from 'axios';

const URLS_PER_PAGE = 50;

export function UrlTable() {
    const [loading, setLoading] = useState(true);
    const [urlPages, setUrlPages] = useState<UrlPages>({});
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    async function fetchPage(pageNum: number): Promise<void> {
        if (pageNum < 1 || pageNum > totalPages)
            return;

        setLoading(true);
        try {
            const response = await axios.get<PaginatedUrlList>(`/api/urls/?page=${pageNum}`);
            setTotalPages(Math.ceil(response.data.count / URLS_PER_PAGE));
            setUrlPages({...urlPages, [pageNum]: response.data.results});
        } catch (err) {
            console.error(err.data);
            setError('Failed to fetch your URLs due to an unexpected error.');
        } finally {
            setLoading(false);
        }
    }

    async function switchPage(pageNum: number) {
        await fetchPage(pageNum);
        setPage(pageNum);
    }

    useEffect(() => {
        fetchPage(1);
    }, []);

    if (error) {
        return <div>{error}</div>;
    }
    if (loading) {
        return <div>Loading...</div>;
    }
    return <div>
        <table>
            <tbody>
            <tr>
                <th>Short</th>
                <th>Long</th>
            </tr>
            {(urlPages[page] || []).map(url => <tr key={url.slug}>
                <td>{url.slug}</td>
                <td>{url.url}</td>
            </tr>)}
            </tbody>
        </table>
        <div>
            <button onClick={() => switchPage(page - 1)}>&lt;</button>
            {page}
            <button onClick={() => switchPage(page + 1)}>&gt;</button>
        </div>
    </div>;
}

interface PaginatedUrlList {
    count: number;
    results: Url[];
    previous: string;
    next: string;
}

interface Url {
    slug: string;
    url: string;
}

interface UrlPages {
    [pageNum: number]: Url[];
}
