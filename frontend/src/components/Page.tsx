import * as React from 'react';
import {Shortener} from './Shortener';
import {UrlTable} from './UrlTable';

export function Page() {
    return <div>
        <Shortener/>
        <UrlTable/>
    </div>;
}
