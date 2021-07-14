import * as React from 'react';
import * as ReactDOM from 'react-dom';
import {Page} from './components/Page';

const container = document.createElement('div');
document.body.appendChild(container);
ReactDOM.render(<Page/>, container);
