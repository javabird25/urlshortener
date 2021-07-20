import {mocked} from 'ts-jest/utils';
import {act, render, screen, waitFor} from '@testing-library/react';
import {Shortener} from '../Shortener';
import React from 'react';
import axios, {AxiosResponse} from 'axios';
import userEvent from '@testing-library/user-event';
import * as slug from '../../slug';

jest.mock('axios');
const axiosMock = mocked(axios, true);

jest.mock('../../slug');
const slugMock = mocked(slug, true);

const SLUG_INPUT_TITLE = 'Shortened URL part';
const URL_INPUT_TITLE = 'URL to shorten';

it('renders with a random slug and an example URL', async () => {
    const slug = '123456';
    slugMock.default.mockResolvedValue(slug);

    act(() => {
        render(<Shortener/>);
    });

    await waitFor(() => {
        expect(slugMock.default).toBeCalledWith(6);
        expect(screen.getByTitle(SLUG_INPUT_TITLE)).toBeTruthy();
        expect(screen.getByTitle(URL_INPUT_TITLE)).toBeTruthy();
    });
});

it('sends a shortening request on button press', async () => {
    const onShortenCallback = jest.fn();
    const slug = 'a_slug';
    const url = 'https://google.com';
    axiosMock.post.mockResolvedValue({data: ''});

    render(<Shortener onShorten={onShortenCallback}/>);

    const slugInput = screen.getByTitle(SLUG_INPUT_TITLE);
    userEvent.clear(slugInput);
    userEvent.type(slugInput, slug);

    const urlInput = screen.getByTitle(URL_INPUT_TITLE);
    userEvent.clear(urlInput);
    userEvent.type(urlInput, url);

    screen.getByRole('button').click();

    await waitFor(() => {
        expect(axiosMock.post).toBeCalledWith('/api/shorten/', {slug, url});
        expect(onShortenCallback).toBeCalled();
    });
});

it('alerts and logs on encountering an unknown server error on shortening request', async () => {
    jest.spyOn(global, 'alert').mockImplementation(() => undefined);
    jest.spyOn(console, 'error').mockImplementation(() => undefined);
    const postResponse = {
        data: '',
        status: 500,
        statusText: 'Internal server error',
    } as AxiosResponse;
    axiosMock.post.mockRejectedValue(postResponse);

    render(<Shortener/>);
    screen.getByRole('button').click();

    await waitFor(() => {
        expect(global.alert).toBeCalledWith(expect.stringContaining('unexpected'));
        expect(console.error).toBeCalledWith(postResponse);
    });
});

it('alerts on "occupied slug" response', async () => {
    axiosMock.post.mockRejectedValue({
        data: '',
        status: 409,
        statusText: 'Conflict',
    } as AxiosResponse);

    render(<Shortener/>);
    screen.getByRole('button').click();

    await waitFor(() => {
        expect(global.alert).toBeCalledWith(expect.stringContaining('occupied'));
    });
});
