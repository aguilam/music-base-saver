export function normalizeTime(totalSeconds: number) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = Math.floor(totalSeconds % 60);
    return { hours, minutes, seconds };
}
  
export function formatTime(totalSeconds: number) {
    const { hours, minutes, seconds } = normalizeTime(totalSeconds);
    const pad = (n: number) => n.toString().padStart(2, "0");
    if (hours > 0) {
        return `${hours}:${pad(minutes)}:${pad(seconds)}`;
    }
    return `${minutes}:${pad(seconds)}`;
}
  
export function formatTimeToString(totalSeconds: number) {
    const { hours, minutes, seconds } = normalizeTime(totalSeconds);
    const parts = [];
    if (hours > 0) parts.push(hours + " hour.");
    if (minutes > 0) parts.push(minutes + " min.");
    if (seconds > 0 || parts.length === 0) parts.push(seconds + " sec.");
    return parts.join(" ");
}