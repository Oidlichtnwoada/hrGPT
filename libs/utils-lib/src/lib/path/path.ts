import * as fs from 'fs';
import * as path from 'path';

export function getAbsolutePathFromRelativeRepoPath(
  relativeRepoPath: string
): string {
  return path.resolve(getAbsoluteRepoRootPath(), relativeRepoPath);
}

export function getAbsoluteRepoRootPath(): string {
  const rootMarkerFile = 'nx.json';
  let currentDirectory = process.cwd();
  while (!fs.readdirSync(currentDirectory).includes(rootMarkerFile)) {
    currentDirectory = path.resolve(currentDirectory, '..');
  }
  return path.resolve(currentDirectory);
}
