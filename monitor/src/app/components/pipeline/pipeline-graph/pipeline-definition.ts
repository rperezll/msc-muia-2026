import { DetectorNodeContent } from '../nodes/detector-node/detector-node';
import { ExplainerNodeContent } from '../nodes/explainer-node/explainer-node';
import { QueueNodeContent } from '../nodes/queue-node/queue-node';
import { SimulatorNodeContent } from '../nodes/simulator-node/simulator-node';

const NODE_W = 256;
const NODE_H = 240;
const GAP_X = 100;
const GAP_Y = 80;

const MAIN_NODE_IDS = ['n1', 'n2', 'n3', 'n4'];

const MAIN_EDGE_DEFS = [
  { id: 'e1', sourceIdx: 0, targetIdx: 1 },
  { id: 'e2', sourceIdx: 1, targetIdx: 2 },
  { id: 'e3', sourceIdx: 2, targetIdx: 3 },
];

export const Dimensions = { NODE_W, NODE_H, GAP_X, GAP_Y };

export const Nodes = { MAIN_NODE_IDS, MAIN_EDGE_DEFS };

export const Definition = {
  nodes: [
    {
      id: 'n1',
      type: 'pipeline-node',
      position: { x: 0, y: 0 },
      data: { label: 'Simulator', type: 'simulator', content: SimulatorNodeContent },
    },
    {
      id: 'n2',
      type: 'pipeline-node',
      position: { x: 300, y: 0 },
      data: { label: 'Detector', type: 'detector', content: DetectorNodeContent },
    },
    {
      id: 'n3',
      type: 'pipeline-node',
      position: { x: 600, y: 0 },
      data: { label: 'Queue', type: 'queue', content: QueueNodeContent },
    },
    {
      id: 'n4',
      type: 'pipeline-node',
      position: { x: 900, y: 0 },
      data: { label: 'Explainer', type: 'explainer', content: ExplainerNodeContent },
    },
  ],
  edges: [
    {
      id: 'e1',
      type: 'animated-edge',
      source: 'n1',
      target: 'n2',
      sourcePort: 'port-right',
      targetPort: 'port-left',
      data: { animated: false },
    },
    {
      id: 'e2',
      type: 'animated-edge',
      source: 'n2',
      target: 'n3',
      sourcePort: 'port-right',
      targetPort: 'port-left',
      data: { animated: false },
    },
    {
      id: 'e3',
      type: 'animated-edge',
      source: 'n3',
      target: 'n4',
      sourcePort: 'port-right',
      targetPort: 'port-left',
      data: { animated: false },
    },
  ],
};
