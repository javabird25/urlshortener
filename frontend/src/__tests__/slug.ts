import {mocked} from 'ts-jest/utils';
import axios, {AxiosResponse} from 'axios';
import randomSlug from '../slug';
import * as randomString from '../random-string';

jest.mock('axios');
const axiosMock = mocked(axios, true);

jest.mock('../random-string');
const randomStringModuleMock = mocked(randomString, true);

it('asks the backend for a slug', async () => {
    const expectedSlug = '123';
    axiosMock.get.mockResolvedValue({data: expectedSlug} as AxiosResponse);

    const actualSlug = await randomSlug(3);

    expect(actualSlug).toEqual(expectedSlug);
    expect(axiosMock.get).toBeCalledWith('/api/slug/?length=3');
});

it('logs and falls back to generating slugs on client side on unexpected /api/slug/ failure', async () => {
    console.error = jest.fn();
    const expectedSlug = '123';
    const response = {data: '', status: 500, statusText: ''} as AxiosResponse
    axiosMock.get.mockRejectedValue(response);
    randomStringModuleMock.default.mockImplementation(() => expectedSlug);

    const actualSlug = await randomSlug(3);

    expect(console.error).toBeCalledWith(response);
    expect(actualSlug).toEqual(expectedSlug);
    expect(randomStringModuleMock.default).toBeCalledWith(3);
});
