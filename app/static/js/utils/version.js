function parseSemanticVersion(version) {
    const normalizedVersion = version.trim().replace(/^v/i, '');
    const match = normalizedVersion.match(/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$/);
    return match ? { core: match.slice(1, 4), prerelease: match[4]?.split('.') || null } : null;
}

function compareNumericIdentifiers(left, right) {
    return left.length - right.length || left.localeCompare(right);
}

export function compareSemanticVersions(leftVersion, rightVersion) {
    const left = parseSemanticVersion(leftVersion);
    const right = parseSemanticVersion(rightVersion);
    if (!left || !right) return null;

    for (let index = 0; index < left.core.length; index++) {
        const comparison = compareNumericIdentifiers(left.core[index], right.core[index]);
        if (comparison !== 0) return comparison;
    }
    if (!left.prerelease && !right.prerelease) return 0;
    if (!left.prerelease) return 1;
    if (!right.prerelease) return -1;

    const sharedLength = Math.min(left.prerelease.length, right.prerelease.length);
    for (let index = 0; index < sharedLength; index++) {
        const leftIdentifier = left.prerelease[index];
        const rightIdentifier = right.prerelease[index];
        if (leftIdentifier === rightIdentifier) continue;
        const leftNumeric = /^\d+$/.test(leftIdentifier);
        const rightNumeric = /^\d+$/.test(rightIdentifier);
        if (leftNumeric && rightNumeric) {
            return compareNumericIdentifiers(leftIdentifier, rightIdentifier);
        }
        if (leftNumeric !== rightNumeric) return leftNumeric ? -1 : 1;
        return leftIdentifier < rightIdentifier ? -1 : 1;
    }
    return left.prerelease.length - right.prerelease.length;
}