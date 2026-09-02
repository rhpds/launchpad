<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=true; section>
  <#if section = "header">
    <style>
      .pf-v5-c-login { display: flex; min-height: 100vh; align-items: center; justify-content: center; }
      .pf-v5-c-login__container { display: block; width: 520px !important; max-width: calc(100vw - 32px) !important; padding: 28px 0; }
      #kc-header { display: none; }
      .pf-v5-c-login__main { border-radius: 16px; box-shadow: 0 18px 48px rgba(0, 0, 0, .34); overflow: hidden; }
      .pf-v5-c-login__main-header { display: block; padding: 32px 40px 16px; }
      .pf-v5-c-login__main-body { padding: 6px 40px 34px; }
      #kc-page-title { width: 100%; margin: 0; text-align: center !important; }
      .launchpad-brand { text-align: center; }
      .launchpad-logos { display: flex; align-items: center; justify-content: center; gap: 26px; min-height: 60px; margin-bottom: 18px; }
      .launchpad-logo-redhat { display: block; width: 74px; height: 54px; object-fit: contain; }
      .launchpad-logo-intel { display: block; width: 124px; height: 50px; object-fit: contain; }
      .launchpad-divider { width: 1px; height: 42px; background: #6a6e73; opacity: .55; }
      .launchpad-title { width: 100%; color: #f0f0f0; font-size: 28px; font-weight: 700; line-height: 1.2; letter-spacing: -.02em; text-align: center; white-space: nowrap; }
      .launchpad-subtitle { width: 100%; color: #c7c7c7; font-size: 15px; font-weight: 400; line-height: 1.5; margin-top: 8px; text-align: center; }
      .launchpad-form { display: grid; gap: 16px; margin-top: 6px; }
      .launchpad-field { display: grid; gap: 8px; }
      .launchpad-label { color: #f0f0f0; font-size: 14px; font-weight: 600; line-height: 1.4; }
      .launchpad-input { box-sizing: border-box; width: 100%; min-height: 46px; padding: 10px 13px; color: #f5f5f5; background: #151515; border: 1px solid #8a8d90; border-radius: 6px; font-size: 16px; }
      .launchpad-input:focus { border-color: #73bcf7; box-shadow: 0 0 0 1px #73bcf7; outline: none; }
      .launchpad-help { color: #a3a3a3; font-size: 13px; line-height: 1.5; margin: -2px 0 0; }
      .launchpad-submit { width: 100%; min-height: 48px; color: #fff; background: #ee0000; border: 1px solid #ee0000; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; }
      .launchpad-submit:hover { background: #cc0000; border-color: #cc0000; }
      @media (max-width: 600px) {
        .pf-v5-c-login__container { padding: 16px 0; }
        .pf-v5-c-login__main-header { padding: 28px 24px 14px; }
        .pf-v5-c-login__main-body { padding: 6px 24px 28px; }
        .launchpad-logos { gap: 20px; }
        .launchpad-title { font-size: 24px; white-space: normal; }
      }
    </style>
    <div class="launchpad-brand">
      <div class="launchpad-logos">
        <img src="${url.resourcesPath}/img/redhat.svg?v=20260902-2" alt="Red Hat" class="launchpad-logo-redhat" />
        <span aria-hidden="true" class="launchpad-divider"></span>
        <img src="${url.resourcesPath}/img/intel.svg?v=20260902-2" alt="Intel" class="launchpad-logo-intel" />
      </div>
      <div class="launchpad-title">Intel × Red Hat AI Launchpad</div>
      <div class="launchpad-subtitle">Secure access to your lab environment</div>
    </div>
  <#elseif section = "form">
    <form id="kc-launchpad-code" class="launchpad-form" action="${url.loginAction}" method="post">
      <input type="hidden" name="order_id" value="${orderId!''}" />
      <div class="launchpad-field"><label class="launchpad-label" for="email">Participant email</label><input class="launchpad-input" id="email" name="email" type="email" autocomplete="email" placeholder="you@company.com" required /></div>
      <div class="launchpad-field"><label class="launchpad-label" for="code">Instructor code</label><input class="launchpad-input" id="code" name="code" autocomplete="one-time-code" placeholder="XXXX-XXXX-XXXX-XXXX-XXXX" required /></div>
      <p class="launchpad-help">Use the email assigned to your seat and the code provided by your instructor. Email ownership is not verified.</p>
      <button class="launchpad-submit" type="submit">Enter lab</button>
    </form>
  </#if>
</@layout.registrationLayout>
