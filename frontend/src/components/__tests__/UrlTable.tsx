import {mocked} from 'ts-jest/utils';
import axios from 'axios';
import {render, waitFor, screen} from '@testing-library/react';
import {UrlTable} from '../UrlTable';
import React from 'react';

jest.mock('axios');
const axiosMock = mocked(axios, true);

it('fetches URLs from /api/urls/ and renders them', async () => {
    axiosMock.get.mockResolvedValue(
        {
            data: {
                results: [
                    {slug: '123', url: 'https://example.com'},
                    {slug: '456', url: 'https://something.com'},
                ],
                count: 2,
                previous: null,
                next: null,
            }
        }
    );

    render(<UrlTable/>);

    await waitFor(() => {
        screen.getByText('Loading...');
    });

    await waitFor(() => {
        screen.getByText('123');
        screen.getByText('456');
        screen.getByText('https://example.com');
        screen.getByText('https://something.com');
        expect(axiosMock.get).toBeCalledWith('/api/urls/?page=1');
    });
});

it.skip('changes the page on "Next page" button click', async () => {
    axiosMock.get
        .mockResolvedValueOnce(
            {
                data: {
                    results: Array.from(Array(50).keys()).map(i => ({url: 'https://example.com', slug: (i + 1).toString()})),
                    count: 60,
                    previous: null,
                    next: null,
                }
            }
        )
        .mockResolvedValueOnce(
            {
                data: {
                    results: Array.from(Array(10).keys()).map(i => ({url: 'https://example.com', slug: (i + 51).toString()})),
                    count: 60,
                    previous: null,
                    next: null,
                }
            }
        );

    render(<UrlTable/>);
    await waitFor(() => { screen.getByText('1'); });
    screen.getByText('>').click();

    await waitFor(() => {
        screen.getByText('51');
    });
});


