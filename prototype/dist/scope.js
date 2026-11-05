// Keep the production brief distinct from this executable local prototype.
const scopeButton = document.createElement('button');
scopeButton.className = 'button';
scopeButton.textContent = 'Prototype scope';
scopeButton.style.marginLeft = 'auto';
document.querySelector('header').append(scopeButton);
scopeButton.onclick = () => modal('What you can try today', `
<p>This working prototype explores the upload → transcription → practice → edit → export flow. It is not the public beta.</p>
<h3>Available</h3><p>MP3, WAV and M4A decoding; up to 100 MB and 5 minutes; Muscriptor note estimation through a local server (requires authorized weights); standard six-string TAB; original and synthesized playback; playback speed; note editing; browser-local projects; MIDI, score JSON and browser PDF printing.</p>
<h3>Still to build and validate</h3><p>Google sign-in, private server storage, lead/rhythm separation, validated automatic note-level technique recognition, validated TuxGuitar .tg exports, weekly account quotas and server-side 30-day deletion.</p>
<p>Local expiry is checked when the app opens; it is not a server retention guarantee. Conversion speed and transcription quality depend on the recording and device. Full mixes may include notes from other instruments.</p>
<h3>Product decisions still open</h3><p>Whether a result with a quality warning consumes a weekly conversion; supported commercial recordings and rights arrangements; launch dates and the final playback-speed range.</p>
<button class="primary full" id="scopeStart">Try uploading a recording →</button>`);
scopeButton.addEventListener('click', () => {
  document.querySelector('#scopeStart').onclick = () => {
    document.querySelector('#modal').close();
    showUpload();
  };
});
document.querySelector('.private').textContent = 'Browser-local prototype';
