export function formatSize(size, nDigits = 1) {
  if (size === 0) return '0 B';
  const k = 1024;
  const digits = nDigits < 0 ? 0 : nDigits;
  const sizes = [' B', ' KB', ' MB', ' GB', ' TB', ' PB'];
  const i = Math.floor(Math.log(size) / Math.log(k));
  return parseFloat((size / Math.pow(k, i)).toFixed(digits)) + sizes[i];
}

export function formatDate(date) {
  date = new Date(date);
  let todaysDate = new Date();
  let prefix = '';
  let options = {};
  if (getDateDiffInDays(todaysDate, date) < 1) {
    prefix = 'Today, ';
    options = { hour: 'numeric', minute: 'numeric' };
  } else if (getDateDiffInDays(date, todaysDate) == 1) {
    prefix = 'Yesterday, ';
    options = { hour: 'numeric', minute: 'numeric' };
  } else if (getDateDiffInDays(date, todaysDate) < 364) {
    options = { month: 'long', day: 'numeric' };
  } else {
    options = { year: 'numeric', month: 'long', day: 'numeric' };
  }
  return prefix + date.toLocaleString(undefined, options);
}

export function formatMimeType(mimeType) {
  const generic = mimeType.split('/')[0];
  const specific = mimeType.split('/')[1];
  let icon = 'file';
  if (['image', 'video', 'audio'].includes(generic)) icon = generic;
  else
    switch (specific) {
      case 'pdf':
        icon = 'pdf';
        break;
    }
  return `${icon}`;
}

export function getDateDiffInDays(date1, date2) {
  const msPerDay = 1000 * 60 * 60 * 24;
  const date1UTC = Date.UTC(
    date1.getFullYear(),
    date1.getMonth(),
    date1.getDate()
  );
  const date2UTC = Date.UTC(
    date2.getFullYear(),
    date2.getMonth(),
    date2.getDate()
  );
  return Math.floor((date1UTC - date2UTC) / msPerDay);
}
